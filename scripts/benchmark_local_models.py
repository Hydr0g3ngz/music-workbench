"""Measure actual isolated workstation tasks. Bundled samples; no network or downloads.

This is a speed/resource benchmark, not an audio-quality evaluation. Each case starts a
new worker, measuring cold worker startup without workstation model reuse. OS file caches are not flushed. Model load,
inference and artifact writing remain included in worker time.
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import psutil
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from music_studio.config import Settings
from music_studio.io import read_json, sha256, write_json
from music_studio.studio.registry import CATALOG, child_environment


def fixtures(root, seconds):
    package = Path(__file__).resolve().parents[1] / "src/music_studio"
    music = np.zeros((round(seconds * 44100), 2), dtype=np.float32)
    for step in range(math.ceil(seconds * 2)):
        for name, gain in (("marimba-72.flac", 0.25), ("kick.flac", 0.22)):
            sample, rate = sf.read(
                package / "data/creation" / name, always_2d=True, dtype="float32"
            )
            if rate != 44100:
                div = math.gcd(rate, 44100)
                sample = resample_poly(sample, 44100 // div, rate // div, axis=0)
            if sample.shape[1] == 1:
                sample = np.repeat(sample, 2, axis=1)
            start = round(step * 0.5 * 44100)
            size = min(len(sample), len(music) - start)
            if size > 0:
                music[start : start + size] += sample[:size] * gain
    sf.write(root / "music.wav", music, 44100, subtype="FLOAT")
    speech, rate = sf.read(package / "ui/speech_demo/noisy.flac", always_2d=True, dtype="float32")
    speech = speech[: round(seconds * rate)]
    div = math.gcd(rate, 44100)
    speech = resample_poly(speech, 44100 // div, rate // div, axis=0)
    sf.write(root / "speech.wav", np.repeat(speech, 2, axis=1), 44100, subtype="FLOAT")


def main(args):
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.input_dir:
        for name in ("music.wav", "speech.wav"):
            shutil.copyfile(args.input_dir / name, root / name)
    else:
        fixtures(root, args.duration)
    env = child_environment(str(args.model_dir.resolve()))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    report = {
        "schema": 1,
        "device_requested": args.device,
        "python": str(args.python),
        "threads": 4,
        "qwen_alignment": args.alignment,
        "cases": [],
        "notes": __doc__.strip(),
    }
    for model in args.models:
        case = root / model
        case.mkdir(exist_ok=True)
        source = root / (
            "speech.wav" if CATALOG[model]["stage"] in ("lyrics", "denoise") else "music.wav"
        )
        config = (
            Settings(model_dir=str(args.model_dir), device=args.device, offline=True, language="en")
            .resolved()
            .model_dump()
        )
        config.update(
            cleanup_strength=1, time_ratio=1, pitch_shift=0, four_stems=model == "demucs-four-stems"
        )
        if model == "qwen3-asr":
            config["lyrics_alignment"] = args.alignment
        if model == "mel-band-roformer-kj" and args.separation_config:
            config["separation_config"] = str(args.separation_config.resolve())
        request = case / "request.json"
        write_json(
            request,
            {
                "input": str(source),
                "input_sha256": sha256(source),
                "output": str(case / "output"),
                "settings": config,
                "model": model,
                "stage": CATALOG[model]["stage"],
                "owner_pid": os.getpid(),
            },
        )
        script = "import sys;sys.path.insert(0,sys.argv.pop(1));"
        script += "from music_studio.io import read_json;from pathlib import Path;"
        script += "from music_studio.studio.task_worker import execute;"
        script += "execute(read_json(Path(sys.argv[1])))"
        print("Running", args.device, model, flush=True)
        start, peak = time.perf_counter(), 0
        with (case / "worker.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                [
                    str(args.python),
                    "-X",
                    "utf8",
                    "-B",
                    "-c",
                    script,
                    str(Path(__file__).resolve().parents[1] / "src"),
                    str(request),
                ],
                stdout=log,
                stderr=log,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            child = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    peak = max(
                        peak,
                        sum(p.memory_info().rss for p in [child, *child.children(recursive=True)]),
                    )
                except psutil.Error:
                    pass
                if time.perf_counter() - start > args.timeout:
                    process.kill()
                    process.wait()
                    break
                time.sleep(0.2)
        elapsed = time.perf_counter() - start
        result = read_json(case / "output/result.json") if process.returncode == 0 else {}
        duration = sf.info(source).duration
        row = {
            "model": model,
            "audio_seconds": round(duration, 3),
            "process_seconds": round(elapsed, 3),
            "realtime_factor": round(elapsed / duration, 3),
            "sampled_peak_rss_mib": round(peak / 1024**2, 1),
            "exit_code": process.returncode,
            "worker_metrics": result.get("metrics"),
            "input_sha256": sha256(source),
        }
        report["cases"].append(row)
        write_json(root / "report.json", report)
        print(json.dumps(row), flush=True)
    if any(row["exit_code"] for row in report["cases"]):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=int, default=30)
    parser.add_argument(
        "--alignment",
        choices=["native", "qwen"],
        default="native",
        help="Qwen coarse recognition or independent acoustic word timing",
    )
    parser.add_argument(
        "--separation-config",
        type=Path,
        help="Explicit RoFormer runtime configuration for reproducible runs",
    )
    parser.add_argument(
        "--input-dir", type=Path, help="Reuse exact frozen WAV bytes for paired runs"
    )
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument(
        "--models", nargs="+", default=["demucs-four-stems", "crepe-rest", "whisper-small"]
    )
    main(parser.parse_args())
