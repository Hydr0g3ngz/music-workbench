"""Immutable, equal-window A/B previews; does not alter arrangement gain or timing."""

import importlib.util
import json
import re
import shutil
from pathlib import Path

import numpy as np
import soundfile as sf
from filelock import FileLock
from pydantic import Field

from ..io import fingerprint, read_json, sha256, write_json
from .models import RevisionRequest
from .service import StudioError

REF = r"^(clip|generation):[a-f0-9]{16}$|^processing:[a-f0-9]{16}:[a-f0-9]{16}$"


class Compare(RevisionRequest):
    a: str = Field(pattern=REF)
    b: str = Field(pattern=REF)
    a_offset: float = Field(default=0, ge=0, le=600)
    b_offset: float = Field(default=0, ge=0, le=600)
    duration: float = Field(default=12, ge=0.4, le=60)


def resolve(service, creation, state, reference):
    kind, identity, *artifact = reference.split(":")
    if kind == "clip":
        clip = next(
            (
                c
                for t in state["content"]["tracks"]
                for c in t["clips"]
                if c["id"] == identity and c["asset"]
            ),
            None,
        )
        if clip:
            return (
                service.asset_path(state["id"], clip["asset"]),
                clip["offset"],
                (clip["duration"]),
                clip["name"],
            )
    elif kind == "generation":
        task = creation.get(state["id"], identity)
        path = creation.audio(state["id"], identity)
        return path, 0, sf.info(path).duration, "ACE-Step · " + task["id"]
    elif kind == "processing" and artifact:
        task = next(
            (
                t
                for t in service.processing(state["id"])
                if t["id"] == identity and t["status"] == "complete"
            ),
            None,
        )
        record = next(
            (
                a
                for a in (task or {}).get("artifacts", [])
                if a["id"] == artifact[0] and a["kind"] == "audio"
            ),
            None,
        )
        if task and record:
            path, meta = service.studio.tasks.artifact_path(task["source_project"], artifact[0])
            if sha256(path) != meta["sha256"]:
                raise StudioError("Candidate audio changed; prepare a new comparison", 409)
            clip = task["source_clip"]
            ratio = task.get("time_ratio", 1) if task["stage"] == "transform" else 1
            return path, clip["offset"] / ratio, clip["duration"] / ratio, record["role"]
    raise StudioError("Audio candidate is not available in this project", 404)


def folder(service, key):
    root = service.studio.root / ".workstation-comparisons"
    if root.is_symlink() or (root / key).is_symlink():
        raise StudioError("Invalid comparison directory")
    path = root / key
    path.mkdir(parents=True, exist_ok=True)
    return path


def prepare(service, creation, key, request):
    state = service.get(key)
    if state["revision"] != request.revision:
        raise StudioError("Session changed; save before comparing", 409)
    sources = [resolve(service, creation, state, ref) for ref in (request.a, request.b)]
    offsets = [request.a_offset, request.b_offset]
    # Round each endpoint once; retain exactly the same number of frames on both sides.
    rate = 44100
    frames = round(
        min(request.duration, *(s[2] - o for s, o in zip(sources, offsets, strict=True))) * rate
    )
    if frames < round(0.4 * rate):
        raise StudioError("Both comparison windows must contain at least 400 ms")
    pinned = [
        {
            "reference": ref,
            "sha256": sha256(source[0]),
            "offset_frames": round((source[1] + offset) * rate),
            "name": source[3],
        }
        for ref, source, offset in zip((request.a, request.b), sources, offsets, strict=True)
    ]
    identity = fingerprint(
        {
            "version": 1,
            "sources": pinned,
            "frames": frames,
            "loudness_runtime": importlib.util.find_spec("pyebur128") is not None,
        }
    )[:32]
    parent = folder(service, key)
    target = parent / identity
    lock = parent / (identity + ".lock")
    if lock.is_symlink() or target.is_symlink():
        raise StudioError("Invalid comparison path")
    with FileLock(str(lock), timeout=60):
        if not target.exists():
            temporary = parent / (identity + ".partial")
            if temporary.exists():
                if temporary.is_symlink() or not temporary.resolve().is_relative_to(
                    parent.resolve()
                ):
                    raise StudioError("Invalid comparison working directory")
                # The per-identity lock excludes an active writer; recover an interrupted render.
                shutil.rmtree(temporary)
            temporary.mkdir()
            try:
                levels = []
                for side, source, info in zip(("a", "b"), sources, pinned, strict=True):
                    with sf.SoundFile(source[0]) as audio:
                        if audio.samplerate != rate or audio.channels != 2:
                            raise StudioError("Comparison requires canonical stereo audio")
                        audio.seek(info["offset_frames"])
                        data = audio.read(frames, dtype="float32", always_2d=True)
                    if len(data) != frames or not np.isfinite(data).all():
                        raise StudioError("Invalid comparison audio range")
                    path = temporary / (side + ".wav")
                    sf.write(path, data, rate, subtype="FLOAT")
                    try:
                        from .loudness import measure

                        measurement = measure(path)
                    except ValueError as error:
                        measurement = {"integrated_lufs": None, "reason": str(error)}
                    levels.append(measurement)
                    info.update(audio_sha256=sha256(path), measurement=measurement)
                available = all(
                    m.get("integrated_lufs") is not None and m.get("true_peak_dbtp") is not None
                    for m in levels
                )
                # Only attenuate, with a common target preserving equal loudness and peak headroom.
                level = (
                    min(
                        *(m["integrated_lufs"] for m in levels),
                        *(m["integrated_lufs"] - max(0, m["true_peak_dbtp"] + 1) for m in levels),
                    )
                    if available
                    else None
                )
                metadata = {
                    "id": identity,
                    "project": key,
                    "duration": frames / rate,
                    "matching_available": available,
                    "target_lufs": level,
                    "method": "Equal-window integrated LUFS; attenuation only; -1 dBTP ceiling",
                    "scope": "Source audio only, before clip/track gains, fades and effects. "
                    "Window offsets are manual; no content or beat alignment is inferred.",
                }
                for side, info in zip(("a", "b"), pinned, strict=True):
                    gain_db = level - info["measurement"]["integrated_lufs"] if available else 0
                    metadata[side] = {
                        **info,
                        "matched_gain": 10 ** (gain_db / 20),
                        "gain_db": gain_db,
                        "url": f"/api/workstation/projects/{key}/comparisons/{identity}/{side}",
                    }
                # A changed input must never populate a content-addressed cache.
                if any(sha256(s[0]) != p["sha256"] for s, p in zip(sources, pinned, strict=True)):
                    raise StudioError("Source audio changed while comparing", 409)
                write_json(temporary / "metadata.json", metadata)
                temporary.rename(target)
            except Exception:
                shutil.rmtree(temporary)
                raise
        metadata = read_json(target / "metadata.json")
    if service.get(key)["revision"] != request.revision:
        raise StudioError("Session changed while preparing; compare again", 409)
    return metadata


def audio(service, key, identity, side):
    service.get(key)
    if not re.fullmatch(r"[a-f0-9]{32}", identity) or side not in ("a", "b"):
        raise StudioError("Comparison does not exist", 404)
    parent = folder(service, key)
    try:
        meta_path = service.studio.safe_file(parent, identity + "/metadata.json")
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        path = service.studio.safe_file(parent, identity + "/" + side + ".wav")
    except (OSError, ValueError) as error:
        raise StudioError("Comparison does not exist", 404) from error
    if sha256(path) != metadata[side]["audio_sha256"]:
        raise StudioError("Comparison audio checksum changed", 409)
    return Path(path)
