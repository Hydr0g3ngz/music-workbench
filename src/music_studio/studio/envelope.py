"""Clip-relative volume envelopes, with amplitude interpolation shared with Web Audio."""

import numpy as np
from pydantic import Field

from .models import StrictModel


class VolumePoint(StrictModel):
    time: float = Field(ge=0, le=600)
    db: float = Field(ge=-60, le=12)


def envelope(times, clip):
    value = np.ones_like(times, dtype=np.float64)
    if clip.fade_in:
        fade = np.clip(times / clip.fade_in, 0, 1)
        value *= np.sin(fade * np.pi / 2) if clip.fade_curve == "equal_power" else fade
    if clip.fade_out:
        fade = np.clip((clip.duration - times) / clip.fade_out, 0, 1)
        value *= np.sin(fade * np.pi / 2) if clip.fade_curve == "equal_power" else fade
    if clip.volume_points:
        value *= np.interp(
            times,
            [p.time for p in clip.volume_points],
            [10 ** (p.db / 20) for p in clip.volume_points],
        )
    return value * 10 ** (clip.gain_db / 20)
