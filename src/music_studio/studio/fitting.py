"""Explicit constant-tempo alignment; an estimated beat is never called a downbeat."""

from typing import Literal

from pydantic import Field

from .models import RevisionRequest, StrictModel
from .service import StudioError


class FitOptions(StrictModel):
    source_bpm: float = Field(ge=30, le=300)
    tempo_multiplier: Literal[0.5, 1, 2] = 1
    source_anchor: float = Field(ge=0, le=600)
    target_beat: float = Field(ge=0, le=3000)


class FitPreview(RevisionRequest):
    clip: str = Field(pattern=r"^[a-f0-9]{16}$")
    fit: FitOptions


def plan(clip, bpm, options):
    effective = options.source_bpm * options.tempo_multiplier
    ratio = bpm / effective
    if not 0.5 <= ratio <= 2:
        raise StudioError("Tempo ratio must be between 0.5 and 2; check half/double-time")
    if not clip["offset"] <= options.source_anchor < clip["offset"] + clip["duration"]:
        raise StudioError("Choose an anchor inside the selected clip's source range")
    anchor_relative = options.source_anchor - clip["offset"]
    target_seconds = options.target_beat * 60 / bpm
    start = target_seconds - anchor_relative / ratio
    duration = clip["duration"] / ratio
    if any(clip.get(fade, 0) / ratio > 30 for fade in ("fade_in", "fade_out")):
        raise StudioError("Slowed fades would exceed 30 seconds; shorten the fades first")
    if start < -1e-9 or start + duration > 600 + 1e-9:
        raise StudioError("Aligned clip exceeds the timeline; move the target or trim the pickup")
    return {
        "version": 1,
        "project_bpm": bpm,
        "options": options.model_dump(),
        "effective_source_bpm": effective,
        "time_ratio": ratio,
        "start": max(0, start),
        "offset": clip["offset"] / ratio,
        "duration": duration,
        "target_seconds": target_seconds,
        "method": "User-confirmed anchor and constant-tempo DSP; no automatic downbeat detection",
    }
