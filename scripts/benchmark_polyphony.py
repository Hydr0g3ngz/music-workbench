"""Frozen GuitarSet development benchmark; run in the managed polyphonic-notes Python.

PYTHONPATH=src <pack>/env/python scripts/benchmark_polyphony.py --data <guitarset>
    --model-dir <pack>/models --output <directory>
No dataset downloads or manually transcribed references are required.
"""

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import mir_eval
import numpy as np

from music_studio.studio.polyphony import MODEL_SHA, extract


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score(reference, notes):
    intervals = np.array([[n[0], n[1]] for n in reference]).reshape(-1, 2)
    pitches = mir_eval.util.midi_to_hz(np.array([n[2] for n in reference]))
    est = np.array([[n.start, n.end] for n in notes]).reshape(-1, 2)
    ep = mir_eval.util.midi_to_hz(np.array([n.pitch for n in notes]))
    values = {}
    for name, ratio in [("onset", None), ("onset_offset", 0.2)]:
        precision, recall, f1, _ = mir_eval.transcription.precision_recall_f1_overlap(
            intervals,
            pitches,
            est,
            ep,
            onset_tolerance=0.05,
            pitch_tolerance=50,
            offset_ratio=ratio,
            offset_min_tolerance=0.05,
        )
        matches = mir_eval.transcription.match_notes(
            intervals,
            pitches,
            est,
            ep,
            onset_tolerance=0.05,
            pitch_tolerance=50,
            offset_ratio=ratio,
            offset_min_tolerance=0.05,
        )
        values[name] = dict(
            precision=precision,
            recall=recall,
            f1=f1,
            missing=len(reference) - len(matches),
            extra=len(notes) - len(matches),
        )
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    suite = json.loads(
        (Path(__file__).resolve().parents[1] / "benchmarks/suite-v1.json").read_text()
    )
    assets = [a for a in suite["assets"] if a["path"].startswith("guitarset/")]
    profiles = {
        "default": dict(note_onset=0.5, note_frame=0.3, note_min_ms=127.7),
        "conservative": dict(note_onset=0.6, note_frame=0.35, note_min_ms=150),
        "sensitive": dict(note_onset=0.35, note_frame=0.25, note_min_ms=100),
    }
    report = {
        "suite": "workbench-polyphony-guitarset-dev-v1",
        "model_sha256": MODEL_SHA,
        "dataset": suite["datasets"]["guitarset"],
        "python": platform.python_version(),
        "platform": platform.platform(),
        "profiles": profiles,
        "cases": [],
        "method": "All six note_midi string annotations; fractional MIDI rounded to nearest "
        "integer. 50 ms onset / 50 cents pitch; offsets 20% or 50 ms. Macro over cases.",
        "limits": [
            "Five frozen accompaniment takes, development suite, not a held-out leaderboard.",
            "Basic Pitch training used GuitarSet: dataset overlap is possible.",
            "No velocity or calibrated probability reference; no velocity accuracy claim.",
            "CPU wall time includes adapter imports and model load per call; no peak RAM claim.",
        ],
    }
    for asset in assets:
        if not asset["path"].endswith(".wav"):
            continue
        wav = args.data / Path(asset["path"]).name
        jam = wav.with_suffix(".jams")
        truth = next(a for a in assets if Path(a["path"]).name == jam.name)
        assert digest(wav) == asset["sha256"] and digest(jam) == truth["sha256"], wav
        data = json.loads(jam.read_text())
        reference = sorted(
            (float(n["time"]), float(n["time"] + n["duration"]), int(round(n["value"])))
            for annotation in data["annotations"]
            if annotation["namespace"] == "note_midi"
            for n in annotation["data"]
            if n["duration"] > 0
        )
        for name, settings in profiles.items():
            folder = args.output / wav.stem / name
            folder.mkdir(parents=True, exist_ok=True)
            started = time.perf_counter()
            result = extract(wav, folder, dict(model_dir=str(args.model_dir), **settings))
            seconds = time.perf_counter() - started
            (folder / "notes.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
            case = dict(
                case=wav.stem,
                profile=name,
                input_sha256=asset["sha256"],
                reference_sha256=truth["sha256"],
                reference_notes=len(reference),
                estimated_notes=len(result.notes),
                seconds=round(seconds, 3),
                scores=score(reference, result.notes),
            )
            report["cases"].append(case)
            print(json.dumps(case), flush=True)
            (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["macro"] = {
        name: {
            metric: float(
                np.mean(
                    [c["scores"][metric]["f1"] for c in report["cases"] if c["profile"] == name]
                )
            )
            for metric in ("onset", "onset_offset")
        }
        for name in profiles
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["macro"]), flush=True)


if __name__ == "__main__":
    main()
