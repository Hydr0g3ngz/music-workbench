"""Replace only a bounded region; model round trips cannot change its surroundings."""

import numpy as np
import soundfile as sf

from ..audio import decode_audio
from ..io import sha256
from .service import StudioError


def splice(reference, generated, target, start, end, blend):
    canonical = target.with_name("repaint-canonical.wav")
    decode_audio(generated, canonical, sha256(generated))
    original, rate = sf.read(reference, dtype="float32", always_2d=True)
    candidate, other_rate = sf.read(canonical, dtype="float32", always_2d=True)
    a, b = round(start * rate), round(end * rate)
    if rate != other_rate or original.shape[1] != candidate.shape[1]:
        raise StudioError("Repaint audio formats differ")
    if not 0 <= a < b <= min(len(original), len(candidate)):
        raise StudioError("Repaint output does not cover the selected region")
    weight = np.ones(b - a, dtype=np.float32)
    n = min(round(blend * rate), (b - a) // 2)
    if n:
        weight[:n] = np.linspace(0, 1, n)
        weight[-n:] = np.linspace(1, 0, n)
    result = original.copy()
    result[a:b] = original[a:b] * (1 - weight[:, None]) + candidate[a:b] * weight[:, None]
    if not np.isfinite(result).all():
        raise StudioError("Repaint output contains invalid samples")
    sf.write(target, result, rate, subtype="FLOAT")
    return {
        "start_frame": a,
        "end_frame": b,
        "sample_rate": rate,
        "blend_frames": n,
        "outside_region_unchanged": True,
        "changed_region_rms": float(np.sqrt(np.mean((result[a:b] - original[a:b]) ** 2))),
    }
