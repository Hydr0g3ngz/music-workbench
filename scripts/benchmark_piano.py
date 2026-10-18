"""Compare pinned Basic Pitch CPU and Transkun CUDA on frozen SMD v2 excerpts.

Download the licensed files separately; this script redistributes no recordings or MIDI.
See docs/piano-notes.en.md for interpretation and the source manifest.
"""

import argparse
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path

import mir_eval
import numpy as np
import pretty_midi
import soundfile as sf

from music_studio.studio.piano_notes import MODEL_SHA as PIANO_SHA
from music_studio.studio.polyphony import MODEL_SHA as BASIC_SHA


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in (
        "data",
        "manifest",
        "output",
        "basic-python",
        "basic-models",
        "piano-python",
        "piano-models",
    ):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    for asset in manifest["assets"]:
        path = args.data / asset["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError(f"Dataset hash mismatch: {path.name}")
    infer = """import json,sys,time
from pathlib import Path
cfg=json.loads(Path(sys.argv[1]).read_text())
if cfg['backend']=='basic-pitch':
 from music_studio.studio.polyphony import extract
else:
 from music_studio.studio.piano_notes import extract
import torch
if cfg['device']=='cuda': torch.cuda.reset_peak_memory_stats()
start=time.perf_counter()
result=extract(Path(cfg['source']),Path(cfg['output']),cfg)
seconds=time.perf_counter()-start
peak=torch.cuda.max_memory_allocated()/2**20 if cfg['device']=='cuda' else None
Path(cfg['output'],'notes.json').write_text(result.model_dump_json(indent=2))
Path(cfg['output'],'metrics.json').write_text(json.dumps({'seconds':seconds,'torch_peak_mib':peak}))
"""
    # Basic Pitch has no Torch dependency: remove the CUDA-only import from its child.
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    report = {
        "suite": "smd-v2-piano-development-v1",
        "dataset": manifest,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu": platform.processor(),
        "models": {
            "basic-pitch": {"version": "0.4.0", "model_sha256": BASIC_SHA, "runtime": "ONNX CPU"},
            "transkun-piano": {
                "version": "2.0.1",
                "model_sha256": PIANO_SHA,
                "runtime": "Torch CUDA FP32",
            },
        },
        "cases": [],
        "method": "Three pieces, two 15 s excerpts at 10 and 40 s. "
        "Only note onsets 0.1–14.9 s enter scoring; offsets clipped at 15 s. "
        "Raw MIDI key-release times; "
        "no CC64 extension or manual alignment. 50 ms onset, 50 cents pitch, 20%/50 ms offset. "
        "Macro average over six excerpts. Raw velocity MAE for onset/pitch matches, "
        "not calibrated confidence.",
        "limits": [
            "Small development suite, not a broad ranking or verified training-disjoint test.",
            "Official SMD v2 synchronization has residual timing limits.",
            "Quality uses identical mono 22050 Hz audio. Speed compares different devices.",
            "Each call reloads the model; wall time includes imports/load. "
            "CUDA context and peak host RAM excluded.",
        ],
    }
    for asset in [a for a in manifest["assets"] if a["path"].endswith(".wav")]:
        piece = asset["path"].removeprefix("mono-").removesuffix(".wav")
        midi = pretty_midi.PrettyMIDI(str(args.data / (piece + ".mid")))
        audio, rate = sf.read(args.data / asset["path"], dtype="float32", always_2d=True)
        for begin in (10, 40):
            case = args.output / f"{piece}-{begin}"
            case.mkdir(exist_ok=True)
            wav = case / "input.wav"
            sf.write(wav, audio[begin * rate : (begin + 15) * rate], rate, subtype="PCM_16")
            reference = sorted(
                (n.start - begin, min(15, n.end - begin), n.pitch, n.velocity)
                for instrument in midi.instruments
                for n in instrument.notes
                if begin + 0.1 <= n.start <= begin + 14.9 and n.end > n.start
            )
            for backend, python, models, device in [
                ("basic-pitch", args.basic_python, args.basic_models, "cpu"),
                ("transkun-piano", args.piano_python, args.piano_models, "cuda"),
            ]:
                folder = case / backend
                folder.mkdir(exist_ok=True)
                config = dict(
                    backend=backend,
                    model_dir=str(models.resolve()),
                    device=device,
                    source=str(wav.resolve()),
                    output=str(folder.resolve()),
                )
                (folder / "request.json").write_text(json.dumps(config))
                if not (folder / "metrics.json").exists():
                    child = infer if device == "cuda" else infer.replace("import torch\n", "")
                    with (folder / "worker.log").open("w", encoding="utf-8") as log:
                        subprocess.run(
                            [str(python), "-X", "utf8", "-c", child, str(folder / "request.json")],
                            env=env,
                            stdout=log,
                            stderr=log,
                            check=True,
                        )
                notes = [
                    n
                    for n in json.loads((folder / "notes.json").read_text())["notes"]
                    if 0.1 <= n["start"] <= 14.9
                ]
                ri = np.array([[n[0], n[1]] for n in reference]).reshape(-1, 2)
                rp = mir_eval.util.midi_to_hz(np.array([n[2] for n in reference]))
                ei = np.array([[n["start"], n["end"]] for n in notes]).reshape(-1, 2)
                ep = mir_eval.util.midi_to_hz(np.array([n["pitch"] for n in notes]))
                row = dict(
                    piece=piece,
                    start=begin,
                    backend=backend,
                    device=device,
                    reference_notes=len(reference),
                    estimated_notes=len(notes),
                    **json.loads((folder / "metrics.json").read_text()),
                )
                for name, offset in (("onset", None), ("onset_offset", 0.2)):
                    precision, recall, f1, _ = mir_eval.transcription.precision_recall_f1_overlap(
                        ri, rp, ei, ep, offset_ratio=offset
                    )
                    row[name] = dict(precision=precision, recall=recall, f1=f1)
                matches = mir_eval.transcription.match_notes(ri, rp, ei, ep, offset_ratio=None)
                row["velocity_mae"] = (
                    float(
                        np.mean([abs(reference[r][3] - notes[e]["velocity"]) for r, e in matches])
                    )
                    if matches
                    else None
                )
                report["cases"].append(row)
                print(piece, begin, backend, row["onset"]["f1"], flush=True)
                (args.output / "report.json").write_text(
                    json.dumps(report, indent=2), encoding="utf-8"
                )
    report["macro"] = {}
    for backend in ("basic-pitch", "transkun-piano"):
        rows = [r for r in report["cases"] if r["backend"] == backend]
        report["macro"][backend] = {
            name: float(np.mean([r[name]["f1"] for r in rows]))
            for name in ("onset", "onset_offset")
        }
        report["macro"][backend].update(
            mean_seconds=float(np.mean([r["seconds"] for r in rows])),
            velocity_mae=float(np.mean([r["velocity_mae"] for r in rows])),
        )
    (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
