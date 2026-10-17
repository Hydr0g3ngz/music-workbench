"""Deterministic timing regression, not an assessment of musical quality.

Run with a Python environment containing the inference/librosa dependencies:
    python scripts/benchmark_material_fit.py --output outputs/benchmark/material-fit
"""

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from music_studio.studio.fitting import FitOptions, plan
from music_studio.studio.musical import transform


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    rate, seconds, bpm = 44100, 12, 100
    beats = np.arange(0.37, seconds - 0.1, 60 / bpm)
    signal = np.zeros(rate * seconds, dtype=np.float32)
    for index, beat in enumerate(beats):
        first = round(beat * rate)
        t = np.arange(round(0.07 * rate)) / rate
        pulse = 0.4 * np.sin(2 * np.pi * (1100 if index % 4 == 0 else 750) * t) * np.exp(-70 * t)
        signal[first : first + len(pulse)] += pulse
    source, target = output / "source-100.wav", output / "fitted-120.wav"
    sf.write(source, np.column_stack([signal, signal]), rate, subtype="FLOAT")
    fitted = plan(
        {"offset": 0, "duration": seconds},
        120,
        FitOptions(source_bpm=bpm, source_anchor=0.37, target_beat=8),
    )
    transform(source, target, fitted["time_ratio"], 0)
    audio, actual_rate = sf.read(target, always_2d=True)
    truth = beats / fitted["time_ratio"]
    measured = []
    for beat in truth:
        first, last = (
            max(0, round((beat - 0.06) * rate)),
            min(len(audio), round((beat + 0.06) * rate)),
        )
        measured.append((first + np.argmax(np.abs(audio[first:last, 0]))) / rate)
    errors = (np.array(measured) - truth) * 1000
    drift = (measured[-1] - measured[0] - (truth[-1] - truth[0])) * 1000
    report = {
        "fixture": "Synthetic decaying sine pulses; exact beat times, not a model output",
        "source_bpm": bpm,
        "project_bpm": 120,
        "source_anchor_seconds": 0.37,
        "source_beat_times": beats.tolist(),
        "fit": fitted,
        "sample_rate": actual_rate,
        "frames": len(audio),
        "max_abs_pulse_peak_error_ms": float(np.max(np.abs(errors))),
        "first_to_last_drift_ms": float(drift),
        "thresholds": {"max_abs_peak_error_ms": 40, "max_abs_drift_ms": 20},
        "passed": bool(
            actual_rate == rate
            and len(audio) == 10 * rate
            and np.max(np.abs(errors)) < 40
            and abs(drift) < 20
        ),
        "limits": "Peak timing is affected by the phase vocoder. A single synthetic fixture "
        "does not measure general beat/downbeat detection or perceptual quality.",
    }
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                k: report[k]
                for k in ("passed", "max_abs_pulse_peak_error_ms", "first_to_last_drift_ms")
            }
        )
    )
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/benchmark/material-fit"))
    run(parser.parse_args().output)
