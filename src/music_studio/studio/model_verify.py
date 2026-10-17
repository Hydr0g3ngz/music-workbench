"""Installation smoke inference on bundled licensed samples, with networking disabled.

This verifies execution and output structure. It is not a model quality benchmark.
"""

import argparse
import os
import socket
from pathlib import Path

import numpy as np
import soundfile as sf

from ..config import Settings
from ..io import read_json, sha256, write_json
from .model_setup import PACKS
from .registry import CATALOG
from .task_worker import execute


def reject_network(*args, **kwargs):
    raise OSError("Installation verification runs offline")


def verify(pack, root):
    socket.socket.connect = reject_network
    socket.socket.connect_ex = reject_network
    folder = root / "verification"
    folder.mkdir(parents=True, exist_ok=True)
    package = Path(__file__).parents[1]
    speech, rate = sf.read(package / "ui/speech_demo/noisy.flac", dtype="float32", always_2d=True)
    from scipy.signal import resample_poly

    speech = resample_poly(speech[: rate * 5], 147, 160, axis=0)
    sf.write(folder / "speech.wav", np.repeat(speech, 2, axis=1), 44100, subtype="FLOAT")
    # Real factory samples exercise non-silent inference, including the Demucs forward pass.
    music = np.zeros((44100 * 4, 2), dtype=np.float32)
    for filename, first in (
        ("marimba-72.flac", 0),
        ("marimba-59.flac", 44100),
        ("marimba-72.flac", 88200),
        ("kick.flac", 0),
        ("snare.flac", 66150),
        ("kick.flac", 88200),
    ):
        sample, rate = sf.read(
            package / "data/creation" / filename, dtype="float32", always_2d=True
        )
        if rate != 44100:
            import math

            divisor = math.gcd(rate, 44100)
            sample = resample_poly(sample, 44100 // divisor, rate // divisor, axis=0)
        if sample.shape[1] == 1:
            sample = np.repeat(sample, 2, axis=1)
        length = min(len(sample), len(music) - first)
        music[first : first + length] += sample[:length] * 0.25
    sf.write(folder / "music.wav", music, 44100, subtype="FLOAT")
    config = Settings(
        model_dir=str(root / "models"), device=PACKS[pack].get("device", "cpu"), offline=True
    ).resolved()
    os.environ["TORCH_HOME"] = str(root / "models/torch")
    report = {}
    for model in PACKS[pack]["models"]:
        print("Offline inference: " + model, flush=True)
        source = folder / (
            "speech.wav" if CATALOG[model]["stage"] in ("lyrics", "denoise") else "music.wav"
        )
        settings = {**config.model_dump(), "cleanup_strength": 1, "time_ratio": 1, "pitch_shift": 0}
        if pack == "vocal-separation":
            settings["separation_config"] = str(root / "separation-runtime.json")
        if pack == "qwen-transcription":
            settings.update(managed_alignment="qwen", language="en", lyrics_alignment="qwen")
        settings["four_stems"] = model == "demucs-four-stems"
        execute(
            {
                "input": str(source),
                "input_sha256": sha256(source),
                "output": str(folder / model),
                "settings": settings,
                "stage": CATALOG[model]["stage"],
                "model": model,
            }
        )
        result = read_json(folder / model / "result.json")
        if pack == "qwen-transcription":
            transcript = read_json(folder / model / "lyrics.json")
            words = [w for line in transcript["segments"] for w in line["words"]]
            if not words or transcript["timing_method"] != "qwen_forced_alignment":
                raise ValueError("Qwen verification did not produce acoustic word timings")
            if any(not 0 <= w["start"] < w["end"] <= len(speech) / 44100 for w in words):
                raise ValueError("Qwen verification returned invalid word timings")
        if (
            PACKS[pack].get("device") == "cuda"
            and not CATALOG[model].get("device")
            and result["metrics"]["device"] != "cuda"
        ):
            raise ValueError("GPU verification did not execute on CUDA")
        if not result["artifacts"]:
            raise ValueError("Verification returned no artifacts")
        for artifact in result["artifacts"]:
            path = folder / model / artifact["file"]
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError("Verification returned an empty artifact")
            if artifact["kind"] == "audio":
                audio, rate = sf.read(path, dtype="float32", always_2d=True)
                if audio.shape != (len(speech) if source.name == "speech.wav" else len(music), 2):
                    raise ValueError("Verification changed audio alignment")
                if rate != 44100 or not np.isfinite(audio).all():
                    raise ValueError("Verification returned invalid audio")
        report[model] = {
            **result["metrics"],
            "offline": True,
            "artifacts": len(result["artifacts"]),
        }
    write_json(folder / "report.json", report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", choices=PACKS, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    verify(args.pack, args.root.resolve())
