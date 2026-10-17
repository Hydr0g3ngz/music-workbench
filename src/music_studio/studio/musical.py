"""Measured material context and reversible DSP, deliberately separate from AI claims."""

from pathlib import Path

import numpy as np
import soundfile as sf

from . import dsp

KEYS = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
PROFILES = {
    "major": np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]),
    "minor": np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]),
}


def key_candidates(chroma):
    energy = np.mean(chroma, axis=1)
    if not np.isfinite(energy).all() or np.std(energy) < 1e-8:
        return []
    scores = []
    for mode, profile in PROFILES.items():
        for tonic, name in enumerate(KEYS):
            scores.append(
                {
                    "key": name + " " + mode,
                    "correlation": float(np.corrcoef(energy, np.roll(profile, tonic))[0, 1]),
                }
            )
    return sorted(scores, key=lambda item: item["correlation"], reverse=True)


def analyze(path: Path):
    import librosa

    y, rate = librosa.load(path, sr=22050, mono=True)
    if len(y) < 2048 or np.max(np.abs(y), initial=0) < 1e-7:
        return {
            "method": "librosa DSP",
            "tempo_bpm": None,
            "beats": [],
            "key": None,
            "key_margin": 0,
            "candidates": [],
            "levels": dsp.inspect_audio(path),
        }
    harmonic, percussive = librosa.effects.hpss(y)
    tempo, frames = librosa.beat.beat_track(y=percussive, sr=rate, trim=False)
    candidates = key_candidates(librosa.feature.chroma_stft(y=harmonic, sr=rate))
    beats = librosa.frames_to_time(frames, sr=rate)
    fit = None
    if len(beats) >= 8:
        slope, intercept = np.polyfit(np.arange(len(beats)), beats, 1)
        residual = np.sqrt(np.mean((beats - intercept - slope * np.arange(len(beats))) ** 2))
        fit = {
            "bpm": float(60 / slope),
            "first_beat_seconds": float(intercept),
            "residual_seconds": float(residual),
            "method": "Least-squares constant-tempo fit to estimated beats; not ground truth",
        }
    return {
        "method": "librosa beat_track + chroma_stft / Krumhansl profiles (DSP)",
        "tempo_bpm": float(np.asarray(tempo).reshape(-1)[0]) if len(frames) >= 2 else None,
        "beats": librosa.frames_to_time(frames, sr=rate).tolist(),
        "beat_grid_fit": fit,
        "key": candidates[0]["key"] if candidates else None,
        "key_margin": candidates[0]["correlation"] - candidates[1]["correlation"]
        if candidates
        else 0,
        "candidates": candidates[:4],
        "levels": dsp.inspect_audio(path),
        "limitations": "Global estimates; not downbeat, chord or melody ground truth. "
        "Half/double tempo, modal ambiguity and modulation may cause errors.",
    }


def transform(source: Path, target: Path, ratio: float, semitones: int):
    import librosa

    data, rate = sf.read(source, dtype="float32", always_2d=True)
    result = data.T
    if ratio != 1:
        result = librosa.effects.time_stretch(result, rate=ratio)
    if semitones:
        result = librosa.effects.pitch_shift(result, sr=rate, n_steps=semitones)
    result = librosa.util.fix_length(result, size=round(len(data) / ratio), axis=-1)
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite transform output")
    sf.write(target, result.T, rate, subtype="FLOAT")
    return {
        "method": "librosa phase vocoder (DSP)",
        "time_ratio": ratio,
        "pitch_shift": semitones,
        "frames": result.shape[-1],
        "warning": "Large changes may smear transients; audition before adoption.",
    }
