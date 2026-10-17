"""Versioned multitrack projects. Source audio and the classic editor stay immutable."""

import hashlib
import io
import json
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Literal

import numpy as np
import soundfile as sf
from fastapi import APIRouter, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute
from pydantic import Field, model_validator

from ..io import fingerprint
from . import dsp, library, midi_import, routing
from . import effects as mix_effects
from .composition import Blueprint, Role
from .envelope import VolumePoint
from .envelope import envelope as clip_envelope
from .fitting import FitOptions
from .models import AudioRange, LocalTaskRequest, RevisionRequest, StrictModel
from .service import StudioError
from .task_range import clip_window

RATE = 44100
ID = r"^[a-f0-9]{16}$"
COLORS = ["#b69aff", "#86c9bc", "#e7b985", "#8cabed", "#d592b5"]


def uid():
    return uuid.uuid4().hex[:16]


class Note(StrictModel):
    pitch: int = Field(ge=0, le=127)
    start: float = Field(ge=0, le=3000)
    length: float = Field(gt=0, le=3000)
    velocity: int = Field(default=90, ge=1, le=127)


class Origin(StrictModel):
    title: str = Field(max_length=500)
    author: str = Field(default="", max_length=1000)
    license: str = Field(default="unspecified", max_length=150)
    source_url: str = Field(default="", max_length=2000)
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    details: str = Field(default="", max_length=3000)


class Clip(StrictModel):
    id: str = Field(pattern=ID)
    group: str | None = Field(default=None, pattern=ID)
    name: str = Field(min_length=1, max_length=150)
    asset: str | None = Field(default=None, pattern=ID)
    start: float = Field(default=0, ge=0, le=600)
    offset: float = Field(default=0, ge=0, le=600)
    duration: float = Field(gt=0, le=600)
    gain_db: float = Field(default=0, ge=-60, le=12)
    fade_in: float = Field(default=0, ge=0, le=30)
    fade_out: float = Field(default=0, ge=0, le=30)
    fade_curve: Literal["linear", "equal_power"] = "linear"
    volume_points: list[VolumePoint] = Field(default_factory=list, max_length=128)
    notes: list[Note] = Field(default_factory=list, max_length=512)
    origin: Origin | None = None

    @model_validator(mode="after")
    def bounds(self):
        if self.start + self.duration > 600 or self.fade_in + self.fade_out > self.duration:
            raise ValueError("Clip end or fade is outside the supported timeline")
        if any(p.time > self.duration for p in self.volume_points) or any(
            b.time <= a.time
            for a, b in zip(self.volume_points, self.volume_points[1:], strict=False)
        ):
            raise ValueError("Volume points must be ordered, unique and inside the clip")
        return self


class Track(StrictModel):
    id: str = Field(pattern=ID)
    name: str = Field(min_length=1, max_length=150)
    kind: Literal["audio", "midi"] = "audio"
    color: str = Field(default=COLORS[0], pattern=r"^#[0-9a-fA-F]{6}$")
    gain_db: float = Field(default=0, ge=-60, le=12)
    pan: float = Field(default=0, ge=-1, le=1)
    mute: bool = False
    solo: bool = False
    instrument: Literal["keys", "bass", "pad", "vcsl-piano", "vcsl-marimba", "vcsl-drums"] = "keys"
    effects: mix_effects.Effects = Field(default_factory=mix_effects.Effects)
    output: str | None = Field(default=None, pattern=ID)
    sends: list[routing.Send] = Field(default_factory=list, max_length=8)
    clips: list[Clip] = Field(default_factory=list, max_length=128)


class Loop(StrictModel):
    enabled: bool = False
    start: float = Field(default=0, ge=0, le=2999.75)
    end: float = Field(default=16, gt=0, le=3000)

    @model_validator(mode="after")
    def bounds(self):
        if self.end - self.start < 0.25:
            raise ValueError("Loop must span at least a quarter beat")
        return self


class Metronome(StrictModel):
    enabled: bool = False
    volume_db: float = Field(default=-18, ge=-48, le=-6)
    accent: bool = True


class Section(StrictModel):
    id: str = Field(pattern=ID)
    name: str = Field(min_length=1, max_length=80)
    start: float = Field(ge=0, le=2999.75)
    end: float = Field(gt=0, le=3000)
    role: Role = "free"
    energy: int | None = Field(default=None, ge=1, le=5)
    intention: str = Field(default="", max_length=240)

    @model_validator(mode="after")
    def bounds(self):
        if self.end - self.start < 0.25:
            raise ValueError("Section must span at least a quarter beat")
        return self


class Arrangement(StrictModel):
    format: Literal["music-studio-arrangement"] = "music-studio-arrangement"
    version: Literal[1] = 1
    title: str = Field(default="Untitled session", min_length=1, max_length=150)
    bpm: float = Field(default=108, ge=30, le=300)
    master_db: float = Field(default=-6, ge=-60, le=6)
    limiter: mix_effects.Limiter = Field(default_factory=mix_effects.Limiter)
    loop: Loop = Field(default_factory=Loop)
    metronome: Metronome = Field(default_factory=Metronome)
    key: str = Field(default="", pattern=r"^$|^(C|C#|D|Eb|E|F|F#|G|Ab|A|Bb|B) (major|minor)$")
    sections: list[Section] = Field(default_factory=list, max_length=64)
    blueprint: Blueprint = Field(default_factory=Blueprint)
    tracks: list[Track] = Field(default_factory=list, max_length=32)
    buses: list[routing.Bus] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def timing_bounds(self):
        routing.validate(self.tracks, self.buses)
        ids = [b.id for b in self.buses] + [
            identity for t in self.tracks for identity in (t.id, *(c.id for c in t.clips))
        ]
        if len(ids) != len(set(ids)):
            raise ValueError("Track, clip and bus identifiers must be unique")
        if self.loop.end * 60 / self.bpm > 600 + 1e-9:
            raise ValueError("Loop end exceeds the 10-minute timeline")
        if any(s.end * 60 / self.bpm > 600 + 1e-9 for s in self.sections):
            raise ValueError("Section exceeds the 10-minute timeline")
        if len({s.id for s in self.sections}) != len(self.sections):
            raise ValueError("Section identifiers must be unique")
        return self


class Save(RevisionRequest):
    content: Arrangement


class Create(StrictModel):
    title: str = Field(default="Untitled session", min_length=1, max_length=150)
    demo: bool = False


class Attach(RevisionRequest):
    source_project: str = Field(pattern=ID)
    asset: str = Field(min_length=1, max_length=80)
    at: float = Field(default=0, ge=0, le=599)


class PatternRequest(RevisionRequest):
    pattern: str = Field(pattern=r"^[a-z0-9-]{1,80}$")
    at: float = Field(default=0, ge=0, le=599)
    use_source_tempo: bool = False


class ProcessClip(RevisionRequest):
    note_onset: float = Field(default=0.5, ge=0.1, le=0.95)
    note_frame: float = Field(default=0.3, ge=0.05, le=0.95)
    note_min_ms: float = Field(default=127.7, ge=40, le=1000)
    clip: str = Field(pattern=ID)
    model: str = Field(min_length=1, max_length=80)
    time_ratio: float = Field(default=1, ge=0.5, le=2)
    pitch_shift: int = Field(default=0, ge=-12, le=12)
    device: Literal["auto", "cpu", "cuda"] = "auto"
    alignment: Literal["auto", "native", "qwen"] = "auto"
    language: str | None = Field(default=None, min_length=2, max_length=12, pattern=r"^[a-zA-Z-]+$")
    strength: float = Field(default=1, ge=0, le=1)
    fit: FitOptions | None = None


def synth_note(times, note, instrument):
    """Deterministic basic oscillator shared in semantics with the browser synth."""
    frequency = 440 * 2 ** ((note.pitch - 69) / 12)
    phase = 2 * np.pi * frequency * times
    tone = (np.sin(phase) + 0.25 * np.sin(phase * 2) + 0.12 * np.sin(phase * 3)) / 1.37
    if instrument == "bass":
        tone = np.sin(phase) * 0.85 + np.sin(phase * 2) * 0.15
    return tone * (0.20 * note.velocity / 127)


class ArrangementService:
    def __init__(self, studio, manager):
        self.studio, self.manager = studio, manager
        with studio.connection() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS arrangements (
                id TEXT PRIMARY KEY, revision INTEGER NOT NULL, content TEXT NOT NULL,
                assets TEXT NOT NULL, past TEXT NOT NULL, future TEXT NOT NULL,
                created REAL NOT NULL, updated REAL NOT NULL, deleted INTEGER NOT NULL DEFAULT 0
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS arrangement_processing (
                task TEXT PRIMARY KEY, session TEXT NOT NULL, source_project TEXT NOT NULL,
                clip TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS arrangement_fits (
                task TEXT PRIMARY KEY, session TEXT NOT NULL, data TEXT NOT NULL
            )""")

    def row(self, db, key, deleted=False):
        if not re.fullmatch(ID, key):
            raise StudioError("Session does not exist", 404)
        row = db.execute("SELECT * FROM arrangements WHERE id=?", (key,)).fetchone()
        if row is None or bool(row["deleted"]) != deleted:
            raise StudioError("Session does not exist", 404)
        return row

    @staticmethod
    def public(row):
        return {
            "id": row["id"],
            "revision": row["revision"],
            "content": json.loads(row["content"]),
            "assets": json.loads(row["assets"]),
            "can_undo": bool(json.loads(row["past"])),
            "can_redo": bool(json.loads(row["future"])),
            "updated": row["updated"],
            "deleted": bool(row["deleted"]),
        }

    def get(self, key):
        with self.studio.connection() as db:
            return self.public(self.row(db, key))

    def list(self, deleted=False):
        with self.studio.connection() as db:
            rows = db.execute(
                "SELECT * FROM arrangements WHERE deleted=? ORDER BY updated DESC", (int(deleted),)
            )
            return [self.public(row) for row in rows]

    def create(self, request):
        key, now = uid(), time.time()
        content = Arrangement(title=request.title)
        with self.studio.transaction() as db:
            db.execute(
                "INSERT INTO arrangements VALUES (?,?,?,?,?,?,?,?,0)",
                (
                    key,
                    0,
                    content.model_dump_json(),
                    "[]",
                    "[]",
                    "[]",
                    now,
                    now,
                ),
            )
        if request.demo:
            self.demo(key)
        return self.get(key)

    def validate(self, content, assets):
        ids, known = set(), {a["id"]: a for a in assets}
        notes = 0
        for track in content.tracks:
            for identity in [track.id, *(c.id for c in track.clips)]:
                if identity in ids:
                    raise StudioError("Track and clip identifiers must be unique")
                ids.add(identity)
            for clip in track.clips:
                notes += len(clip.notes)
                if track.kind == "audio":
                    asset = known.get(clip.asset)
                    if not asset or clip.notes:
                        raise StudioError("Audio clip needs a registered audio asset")
                    if clip.offset + clip.duration > asset["duration"] + 1 / RATE:
                        raise StudioError("Clip range exceeds source audio")
                elif clip.asset:
                    raise StudioError("MIDI clips contain notes, not audio asset references")
        if notes > 8192:
            raise StudioError("Session supports at most 8192 notes")

    def update(self, key, revision, content, new_asset=None, new_assets=()):
        with self.studio.transaction() as db:
            row = self.row(db, key)
            assets = json.loads(row["assets"])
            if new_asset and new_asset.get("import_id"):
                existing = self.imported(assets, new_asset["import_id"], new_asset["import_hash"])
                if existing:
                    return self.public(row)
            self.studio._check_revision(row, revision)
            for candidate in ([new_asset] if new_asset else []) + list(new_assets):
                if candidate["id"] not in {a["id"] for a in assets}:
                    if len(assets) >= 256:
                        raise StudioError("Session asset limit reached")
                    assets.append(candidate)
            self.validate(content, assets)
            past = [*json.loads(row["past"]), json.loads(row["content"])][-60:]
            db.execute(
                "UPDATE arrangements SET content=?, assets=?, past=?, future='[]', "
                "revision=revision+1, updated=? WHERE id=?",
                (
                    content.model_dump_json(),
                    json.dumps(assets),
                    json.dumps(past),
                    time.time(),
                    key,
                ),
            )
        return self.get(key)

    def history(self, key, revision, direction):
        if direction not in ("undo", "redo"):
            raise StudioError("Unknown history direction")
        with self.studio.transaction() as db:
            row = self.row(db, key)
            self.studio._check_revision(row, revision)
            past, future = json.loads(row["past"]), json.loads(row["future"])
            source, target = (past, future) if direction == "undo" else (future, past)
            if not source:
                raise StudioError("No further history", 409)
            target.append(json.loads(row["content"]))
            content = source.pop()
            db.execute(
                "UPDATE arrangements SET content=?, past=?, future=?, "
                "revision=revision+1, updated=? WHERE id=?",
                (
                    json.dumps(content),
                    json.dumps(past[-60:]),
                    json.dumps(future[-60:]),
                    time.time(),
                    key,
                ),
            )
        return self.get(key)

    def trash(self, key, revision, restore=False):
        with self.studio.transaction() as db:
            row = self.row(db, key, deleted=restore)
            self.studio._check_revision(row, revision)
            db.execute(
                "UPDATE arrangements SET deleted=?, revision=revision+1, updated=? WHERE id=?",
                (0 if restore else 1, time.time(), key),
            )
        return {"id": key, "deleted": not restore}

    def attach(self, key, request, origin=None, import_meta=None):
        state = self.get(key)
        if state["revision"] != request.revision:
            raise StudioError("Session changed; reload before importing", 409)
        path = self.studio.asset_path(request.source_project, request.asset)
        info = dsp.inspect_audio(path)
        if info["sample_rate"] != RATE or info["channels"] != 2:
            raise StudioError("Source must use the canonical stereo timeline")
        if info["duration"] <= 0 or request.at + info["duration"] > 600:
            raise StudioError("This preview supports sessions up to 10 minutes")
        asset = {
            "id": fingerprint({"project": request.source_project, "asset": request.asset})[:16],
            "source_project": request.source_project,
            "source_asset": request.asset,
            "name": self.manager.record(request.source_project)["title"],
            "duration": info["duration"],
            "waveform": dsp.peaks(path, 480),
        }
        if import_meta:
            asset.update(import_meta)
        if request.asset.startswith("asset:"):
            registered = self.studio.registered_assets(request.source_project)
            match = next((a for a in registered if "asset:" + a["id"] == request.asset), None)
            if match:
                asset["name"] = match["role"]
        content = Arrangement.model_validate(state["content"])
        content.tracks.append(
            Track(
                id=uid(),
                name=asset["name"],
                color=COLORS[len(content.tracks) % len(COLORS)],
                clips=[
                    Clip(
                        id=uid(),
                        name=asset["name"],
                        asset=asset["id"],
                        start=request.at,
                        duration=asset["duration"],
                        origin=origin,
                    )
                ],
            )
        )
        # Revalidation applies list limits after appending.
        content = Arrangement.model_validate(content.model_dump())
        return self.update(key, request.revision, content, asset)

    def process_clip(self, key, request):
        state = self.get(key)
        if state["revision"] != request.revision:
            raise StudioError("Session changed; reload before processing", 409)
        clip = next(
            (c for t in state["content"]["tracks"] for c in t["clips"] if c["id"] == request.clip),
            None,
        )
        if not clip or not clip["asset"]:
            raise StudioError("Select an audio clip")
        fit = None
        if request.fit:
            from .fitting import plan

            if request.model != "time-pitch":
                raise StudioError("Beat alignment applies only to time/pitch candidates")
            fit = plan(clip, state["content"]["bpm"], request.fit)
            request.time_ratio = fit["time_ratio"]
        asset = next(a for a in state["assets"] if a["id"] == clip["asset"])
        source_project = asset["source_project"]
        task = self.studio.tasks.submit(
            source_project,
            LocalTaskRequest(
                revision=self.studio.session(source_project)["revision"],
                model=request.model,
                asset=asset["source_asset"],
                range=AudioRange(start=clip["offset"], end=clip["offset"] + clip["duration"]),
                time_ratio=request.time_ratio,
                pitch_shift=request.pitch_shift,
                device=request.device,
                alignment=request.alignment,
                language=request.language,
                strength=request.strength,
                note_onset=request.note_onset,
                note_frame=request.note_frame,
                note_min_ms=request.note_min_ms,
            ),
        )
        with self.studio.transaction() as db:
            db.execute(
                "INSERT INTO arrangement_processing VALUES (?,?,?,?)",
                (task["id"], key, source_project, json.dumps(clip)),
            )
            if fit:
                db.execute(
                    "INSERT INTO arrangement_fits VALUES (?,?,?)",
                    (task["id"], key, json.dumps(fit)),
                )
        return task

    def fit_preview(self, key, request):
        from .fitting import plan

        state = self.get(key)
        if state["revision"] != request.revision:
            raise StudioError("Session changed; save before fitting", 409)
        clip = next(
            (
                c
                for t in state["content"]["tracks"]
                for c in t["clips"]
                if c["id"] == request.clip and c["asset"]
            ),
            None,
        )
        if not clip:
            raise StudioError("Select an audio clip")
        return plan(clip, state["content"]["bpm"], request.fit)

    def processing(self, key):
        self.get(key)
        with self.studio.connection() as db:
            rows = list(
                db.execute(
                    "SELECT p.*,f.data AS fit FROM arrangement_processing p "
                    "LEFT JOIN arrangement_fits f ON p.task=f.task AND p.session=f.session "
                    "WHERE p.session=?",
                    (key,),
                )
            )
        return [
            {
                **self.studio.tasks.get(r["source_project"], r["task"]),
                "source_project": r["source_project"],
                "source_clip": json.loads(r["clip"]),
                "fit": json.loads(r["fit"]) if r["fit"] else None,
            }
            for r in rows
        ]

    def adopt_stems(self, key, task_id, revision):
        from ..io import sha256

        state = self.get(key)
        if state["revision"] != revision:
            raise StudioError("Session changed; reload before adopting stems", 409)
        task = next((t for t in self.processing(key) if t["id"] == task_id), None)
        if (
            not task
            or task["status"] != "complete"
            or task["stage"] not in ("separate", "transform")
        ):
            raise StudioError("Completed separation or time/pitch task required")
        content = Arrangement.model_validate(state["content"])
        if task.get("fit") and content.bpm != task["fit"]["project_bpm"]:
            raise StudioError("Project tempo changed; prepare a new beat-fit candidate", 409)
        pair = next(
            ((t, c) for t in content.tracks for c in t.clips if c.id == task["source_clip"]["id"]),
            None,
        )
        if not pair or pair[1].model_dump() != task["source_clip"]:
            raise StudioError(
                "Source clip changed or was removed; undo its edits before replacing", 409
            )
        track, clip = pair
        artifacts = {a["role"]: a for a in task["artifacts"] if a["kind"] == "audio"}
        roles = (
            ("transformed",)
            if task["stage"] == "transform"
            else ("drums", "bass", "vocals", "other")
            if task["model"] == "demucs-four-stems"
            else ("vocals", "instrumental")
        )
        if set(artifacts) != set(roles):
            raise StudioError("All aligned results are required")
        additions = []
        for role in roles:
            artifact = artifacts[role]
            path, record = self.studio.tasks.artifact_path(task["source_project"], artifact["id"])
            if sha256(path) != record["sha256"]:
                raise StudioError("Stem checksum changed")
            info = dsp.inspect_audio(path)
            ratio = task.get("time_ratio", 1) if task["stage"] == "transform" else 1
            if any(
                info[f] != task["input_audio"][f] for f in ("frames", "sample_rate", "channels")
            ) and not (
                task["stage"] == "transform"
                and info["sample_rate"] == RATE
                and info["channels"] == 2
                and abs(info["frames"] - round(task["input_audio"]["frames"] / ratio)) <= 1
            ):
                raise StudioError("Stem timeline does not match the input")
            identity = fingerprint(
                {"project": task["source_project"], "asset": "asset:" + artifact["id"]}
            )[:16]
            additions.append(
                {
                    "id": identity,
                    "source_project": task["source_project"],
                    "source_asset": "asset:" + artifact["id"],
                    "name": role,
                    "duration": info["duration"],
                    "waveform": dsp.peaks(path, 480),
                }
            )
            replacement = clip.model_copy(deep=True)
            replacement.id, replacement.asset, replacement.name = uid(), identity, role
            replacement.offset, replacement.duration = clip_window(task)
            scale = 1 / ratio
            replacement.fade_in *= scale
            replacement.fade_out *= scale
            # A rounded audio boundary may be up to one sample shorter than the UI trim.
            if replacement.fade_in + replacement.fade_out > replacement.duration:
                fade_scale = replacement.duration / (replacement.fade_in + replacement.fade_out)
                replacement.fade_in *= fade_scale
                replacement.fade_out = replacement.duration - replacement.fade_in
            for point in replacement.volume_points:
                point.time = (
                    replacement.duration
                    if point.time == clip.duration
                    else min(replacement.duration, point.time * scale)
                )
            if task["stage"] == "transform":
                replacement.name = clip.name + " · fitted"
                if task.get("fit"):
                    replacement.start = task["fit"]["start"]
            spec = self.studio.tasks.registry.spec(task["model"])
            replacement.origin = Origin(
                title=clip.name + " · " + role,
                author=clip.origin.author if clip.origin else "",
                license=clip.origin.license if clip.origin else "unspecified",
                source_url=clip.origin.source_url if clip.origin else "",
                sha256=record["sha256"],
                details=(
                    f"Processor {task['model']}; model license {spec['license']}; "
                    + f"{spec['source']}. "
                    + "Separation task "
                    + task_id
                    + "; source "
                    + task["input_sha256"]
                    + (
                        "; source range " + json.dumps(task["source_range"])
                        if task.get("source_range")
                        else ""
                    )
                    + ("; beat fit " + json.dumps(task["fit"]) if task.get("fit") else "")
                    + (
                        ". Original attribution: " + clip.origin.model_dump_json()
                        if clip.origin
                        else ""
                    )
                )[:3000],
            )
            stem_track = track.model_copy(deep=True)
            stem_track.id, stem_track.name, stem_track.clips = uid(), role, [replacement]
            if task["stage"] == "transform":
                stem_track.name = track.name + " · fitted"
            stem_track.color = COLORS[(len(content.tracks) + len(additions)) % len(COLORS)]
            content.tracks.append(stem_track)
        track.clips.remove(clip)
        if not track.clips:
            content.tracks.remove(track)
        content = Arrangement.model_validate(content.model_dump())
        return self.update(key, revision, content, new_assets=additions)

    @staticmethod
    def imported(assets, import_id, digest):
        existing = next((a for a in assets if a.get("import_id") == import_id), None)
        if existing and existing["import_hash"] != digest:
            raise StudioError("Import identifier already belongs to a different recording", 409)
        return existing

    def import_file(self, key, revision, upload, at=0, import_id=None):
        state = self.get(key)
        upload.file.seek(0, 2)
        if upload.file.tell() > 256 * 1024 * 1024:
            raise StudioError("Audio upload limit is 256 MiB", 413)
        upload.file.seek(0)
        meta = None
        if import_id:
            digest = hashlib.sha256()
            while chunk := upload.file.read(1024 * 1024):
                digest.update(chunk)
            upload.file.seek(0)
            digest = fingerprint({"sha256": digest.hexdigest(), "at": at})
            if self.imported(state["assets"], import_id, digest):
                return state
            meta = {"import_id": import_id, "import_hash": digest}
        if state["revision"] != revision:
            raise StudioError("Session changed; save or reload before importing", 409)
        if len(state["content"]["tracks"]) >= 32:
            raise StudioError("This preview supports at most 32 tracks")
        record = self.import_stream(upload.filename or "audio.wav", upload.file)
        return self.attach(
            key,
            Attach(revision=revision, source_project=record["id"], asset="source", at=at),
            import_meta=meta,
        )

    def import_stream(self, name, stream):
        record, destination = self.manager.create(name)
        with destination.open("xb") as output:
            shutil.copyfileobj(stream, output, 1024 * 1024)
        return record

    def add_pattern(self, key, request):
        state = self.get(key)
        pattern = next(
            (p for p in library.manifest()["patterns"] if p["id"] == request.pattern), None
        )
        if pattern is None:
            raise StudioError("Drum pattern does not exist", 404)
        content = Arrangement.model_validate(state["content"])
        if request.use_source_tempo:
            if content.tracks:
                raise StudioError("Source tempo can only be adopted by an empty session")
            content.bpm = pattern["bpm"]
        content.tracks.append(
            Track(
                id=uid(),
                name=pattern["title"],
                kind="midi",
                instrument="vcsl-drums",
                color=COLORS[2],
                gain_db=-3,
                clips=[
                    Clip(
                        id=uid(),
                        name=pattern["title"],
                        start=request.at,
                        duration=pattern["beats"] * 60 / content.bpm,
                        notes=pattern["notes"],
                        origin=pattern["origin"],
                    )
                ],
            )
        )
        return self.update(key, request.revision, Arrangement.model_validate(content.model_dump()))

    @staticmethod
    def midi_bytes(upload):
        upload.file.seek(0)
        raw = upload.file.read(8 * 1024 * 1024 + 1)
        return raw, midi_import.inspect_midi(raw)

    def import_midi(self, key, revision, upload, at=0, use_source_tempo=False):
        state = self.get(key)
        if revision != state["revision"]:
            raise StudioError("Session changed; save before importing MIDI", 409)
        raw, parsed = self.midi_bytes(upload)
        content = Arrangement.model_validate(state["content"])
        if not 0 <= at <= 599:
            raise StudioError("Invalid MIDI insertion position")
        if use_source_tempo:
            if content.tracks:
                raise StudioError("Source tempo can only be adopted by an empty session")
            if not 30 <= parsed["bpm"] <= 300:
                raise StudioError("Source BPM is outside 30–300; use the current project tempo")
            content.bpm = parsed["bpm"]
        import hashlib

        from ..io import sha256

        identity = hashlib.sha256(raw).hexdigest()
        folder = self.studio.root / ".midi-originals"
        if folder.is_symlink():
            raise StudioError("Invalid MIDI archive directory")
        folder.mkdir(exist_ok=True)
        original = folder / f"{identity}.mid"
        if not original.exists():
            with original.open("xb") as output:
                output.write(raw)
        if original.is_symlink() or sha256(original) != identity:
            raise StudioError("MIDI archive checksum mismatch")
        origin = Origin(
            title=Path(upload.filename or "Imported MIDI").name[:500],
            sha256=identity,
            details="Original performance seconds preserved on the project beat grid. "
            "Tempo map flattened; instrument mapping and CC64 sustain applied. "
            "Pitch bends and other controller automation are not imported. "
            + ", ".join(parsed["warnings"]),
        )
        for part in midi_import.parts(parsed, content.bpm, at):
            content.tracks.append(
                Track(
                    id=uid(),
                    name=part["name"],
                    kind="midi",
                    instrument=part["instrument"],
                    color=COLORS[len(content.tracks) % len(COLORS)],
                    gain_db=-3,
                    clips=[
                        Clip(id=uid(), name=part["name"], origin=origin, **clip)
                        for clip in part["clips"]
                    ],
                )
            )
        updated = self.update(key, revision, Arrangement.model_validate(content.model_dump()))
        return {**updated, "midi_import": midi_import.summary(parsed)}

    def credits(self, key):
        state = self.get(key)
        lines = [state["content"]["title"], "Music Workbench — Sources / 素材来源", ""]
        used = set()
        for track in state["content"]["tracks"]:
            if track["kind"] == "midi" and track["instrument"] in library.SAMPLED:
                used.add(
                    json.dumps(library.manifest()["origin"], ensure_ascii=False, sort_keys=True)
                )
            for clip in track["clips"]:
                if clip.get("origin"):
                    used.add(json.dumps(clip["origin"], ensure_ascii=False, sort_keys=True))
        for entry in sorted(used):
            source = json.loads(entry)
            lines.extend(
                f"{field}: {source[field]}"
                for field in ("title", "author", "license", "source_url", "details")
                if source.get(field)
            )
            lines.append("")
        return "\n".join(lines)

    def adopt_melody(self, key, task_id, revision):
        from ..io import read_json, sha256

        state = self.get(key)
        if state["revision"] != revision:
            raise StudioError("Session changed; reload before adopting notes", 409)
        task = next((t for t in self.processing(key) if t["id"] == task_id), None)
        if not task or task["stage"] != "melody" or task["status"] != "complete":
            raise StudioError("Completed melody task required")
        artifact = next(a for a in task["artifacts"] if a["role"] == "melody")
        path, record = self.studio.tasks.artifact_path(task["source_project"], artifact["id"])
        if sha256(path) != record["sha256"]:
            raise StudioError("Melody checksum changed")
        source = Clip.model_validate(task["source_clip"])
        offset, _ = clip_window(task)
        beat = 60 / state["content"]["bpm"]
        notes = []
        for n in read_json(path)["notes"]:
            start = max(n["start"], offset)
            end = min(n["end"], offset + source.duration)
            if end <= start:
                continue
            notes.append(
                Note(
                    pitch=n["pitch"],
                    start=(start - offset) / beat,
                    length=(end - start) / beat,
                    velocity=n.get("velocity", 80),
                )
            )
        if not notes:
            raise StudioError("No melody notes within this clip")
        if len(notes) > 512:
            raise StudioError("More than 512 notes; use a shorter source clip")
        content = Arrangement.model_validate(state["content"])
        spec = self.studio.tasks.registry.spec(task["model"])
        content.tracks.append(
            Track(
                id=uid(),
                name=source.name + " · notes",
                kind="midi",
                instrument="vcsl-piano" if task["model"] == "basic-pitch" else "vcsl-marimba",
                gain_db=-9,
                color=COLORS[len(content.tracks) % len(COLORS)],
                clips=[
                    Clip(
                        id=uid(),
                        name=source.name + " · notes",
                        start=source.start,
                        duration=source.duration,
                        notes=notes,
                        origin=Origin(
                            title=source.name + " · estimated notes",
                            author=source.origin.author if source.origin else "",
                            source_url=source.origin.source_url if source.origin else "",
                            sha256=record["sha256"],
                            license=source.origin.license if source.origin else "unspecified",
                            details=(
                                f"{task['model']}; {spec['source']}; task {task_id}; "
                                "Estimated editable notes, not score ground truth. "
                                + (source.origin.details if source.origin else "")
                            )[:3000],
                        ),
                    )
                ],
            )
        )
        return self.update(key, revision, Arrangement.model_validate(content.model_dump()))

    def asset_path(self, key, identity):
        asset = next((a for a in self.get(key)["assets"] if a["id"] == identity), None)
        if not asset:
            raise StudioError("Session asset does not exist", 404)
        return self.studio.asset_path(asset["source_project"], asset["source_asset"])

    def demo(self, key):
        state = self.get(key)
        bpm, bars = 108, 8
        beat, duration = 60 / bpm, bars * 4 * 60 / bpm
        t = np.arange(round(duration * RATE)) / RATE
        drums = np.zeros_like(t)
        rng = np.random.default_rng(108)
        for n in range(bars * 8):
            at = round(n * beat / 2 * RATE)
            count = min(round(0.18 * RATE), len(t) - at)
            local = np.arange(count) / RATE
            hat = rng.uniform(-1, 1, count) * np.exp(-local * 70) * 0.09
            drums[at : at + count] += hat
            if n % 2 == 0:
                kick = np.sin(2 * np.pi * (48 * local + 0.9 * (1 - np.exp(-local * 35))))
                drums[at : at + count] += kick * np.exp(-local * 23) * 0.42
            if n % 4 == 2:
                drums[at : at + count] += rng.uniform(-1, 1, count) * np.exp(-local * 28) * 0.2
        data = io.BytesIO()
        sf.write(data, np.column_stack([drums, drums]), RATE, format="WAV", subtype="FLOAT")
        data.seek(0)
        record = self.import_stream("01 - Dusty drums.wav", data)
        state = self.attach(
            key, Attach(revision=state["revision"], source_project=record["id"], asset="source")
        )
        content = Arrangement.model_validate(state["content"])
        if content.title == "Untitled session":
            content.title = "Midnight Sketch"
        content.tracks[0].name = "Dusty drums"
        content.tracks[0].color = COLORS[2]
        content.tracks[0].gain_db = -3
        for name, instrument, color, gain in [
            ("Velvet keys", "keys", COLORS[0], -1),
            ("Warm bass", "bass", COLORS[1], -1),
            ("Air & texture", "pad", COLORS[3], -8),
        ]:
            notes = []
            for bar in range(bars):
                root = [57, 53, 60, 55][bar % 4]
                if instrument == "keys":
                    for step in range(4):
                        for interval in [0, 3, 7]:
                            notes.append(
                                Note(
                                    pitch=root + 12 + interval,
                                    start=bar * 4 + step,
                                    length=0.75,
                                    velocity=78 + step * 3,
                                )
                            )
                elif instrument == "bass":
                    for step in [0, 1.5, 2, 3.5]:
                        notes.append(
                            Note(pitch=root - 12, start=bar * 4 + step, length=0.45, velocity=100)
                        )
                else:
                    for interval in [0, 7]:
                        notes.append(
                            Note(pitch=root + interval, start=bar * 4, length=3.8, velocity=75)
                        )
            content.tracks.append(
                Track(
                    id=uid(),
                    name=name,
                    kind="midi",
                    color=color,
                    gain_db=gain,
                    instrument=instrument,
                    clips=[
                        Clip(id=uid(), name=name, duration=duration, fade_out=0.08, notes=notes)
                    ],
                )
            )
        self.update(key, state["revision"], content)

    def export(self, key, revision, kind):
        state = self.get(key)
        if revision != state["revision"]:
            raise StudioError("Session changed; save before exporting", 409)
        content = Arrangement.model_validate(state["content"])
        folder = self.studio.root / ".arrangement-exports"
        if folder.is_symlink():
            raise StudioError("Invalid export directory")
        folder.mkdir(exist_ok=True)
        identity = uid()
        target = folder / f"{identity}.{kind}"
        if kind not in ("mid", "wav"):
            raise StudioError("Unsupported export format")
        measurements = None
        try:
            if kind == "mid":
                self.export_midi(content, target)
            else:
                self.render(key, content, target)
                measurements = {"levels": dsp.inspect_audio(target)}
                try:
                    from .loudness import measure

                    measurements["loudness"] = measure(target)
                except (ImportError, ValueError) as error:
                    measurements["loudness_unavailable"] = str(error)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return {
            "url": f"/api/workstation/exports/{identity}.{kind}",
            "revision": revision,
            "name": content.title,
            "kind": kind,
            "measurements": measurements,
        }

    def render(self, key, content, target):
        from contextlib import ExitStack

        end = max((c.start + c.duration for t in content.tracks for c in t.clips), default=0)
        if not end:
            raise StudioError("Add a clip before exporting")
        active = [t for t in content.tracks if routing.audible(t, content.tracks)]
        end = max(
            end,
            max(
                (
                    c.start + c.duration + routing.tail(t, content.buses)
                    for t in active
                    for c in t.clips
                ),
                default=0,
            ),
        )
        racks = {t.id: mix_effects.Rack(t.effects, RATE) for t in active}
        bus_racks = {b.id: mix_effects.Rack(b.effects, RATE) for b in content.buses}
        limiter = mix_effects.OutputLimiter(content.limiter, RATE)
        with ExitStack() as stack:
            assets = {
                a["id"]: stack.enter_context(sf.SoundFile(self.asset_path(key, a["id"])))
                for a in self.get(key)["assets"]
            }
            output = stack.enter_context(
                sf.SoundFile(target, "w", samplerate=RATE, channels=2, subtype="PCM_24")
            )
            for base in range(0, round(end * RATE), 16384):
                count = min(16384, round(end * RATE) - base)
                mixed = np.zeros((count, 2), dtype=np.float64)
                buses = {b.id: np.zeros_like(mixed) for b in content.buses}
                for track in active:
                    track_mix = np.zeros((count, 2), dtype=np.float64)
                    for clip in track.clips:
                        start = max(base, round(clip.start * RATE))
                        stop = min(base + count, round((clip.start + clip.duration) * RATE))
                        if stop <= start:
                            continue
                        relative = (np.arange(start, stop) - round(clip.start * RATE)) / RATE
                        if track.kind == "audio":
                            asset = assets[clip.asset]
                            asset.seek(round(clip.offset * RATE) + start - round(clip.start * RATE))
                            data = asset.read(stop - start, dtype="float64", always_2d=True)
                            if len(data) != stop - start:
                                raise StudioError("Source audio changed during export")
                        else:
                            if track.instrument in library.SAMPLED:
                                data = library.midi_audio(
                                    relative + clip.offset, clip, content.bpm, track.instrument
                                )
                            else:
                                data = self.synth_block(
                                    relative + clip.offset, clip, content.bpm, track.instrument
                                )
                        envelope = clip_envelope(relative, clip)
                        track_mix[start - base : stop - base] += data * envelope[:, None]
                    track_mix = racks[track.id].process(track_mix)
                    signal = dsp.balance(track_mix, track.pan) * 10 ** (track.gain_db / 20)
                    if track.output:
                        buses[track.output] += signal
                    elif not any(b.solo for b in content.buses):
                        mixed += signal
                    for send in track.sends:
                        if send.enabled:
                            buses[send.bus] += signal * 10 ** (send.gain_db / 20)
                for bus in content.buses:
                    signal = bus_racks[bus.id].process(buses[bus.id])
                    if routing.bus_audible(bus, content.buses):
                        mixed += dsp.balance(signal, bus.pan) * 10 ** (bus.gain_db / 20)
                mixed = limiter.process(mixed * 10 ** (content.master_db / 20))
                if not np.isfinite(mixed).all() or np.max(np.abs(mixed), initial=0) >= 1:
                    raise StudioError(
                        "Master exceeds 0 dBFS; lower the master fader and export again"
                    )
                output.write(mixed)

    @staticmethod
    def synth_block(times, clip, bpm, instrument):
        mono = np.zeros(len(times))
        beat = 60 / bpm
        for note in clip.notes:
            if (
                not len(times)
                or note.start * beat > times[-1]
                or (note.start + note.length) * beat <= times[0]
            ):
                continue
            local = times - note.start * beat
            length = note.length * beat
            mask = (local >= 0) & (local < length)
            x = local[mask]
            attack = 0.08 if instrument == "pad" else 0.008
            envelope = np.minimum(x / attack, 1) * np.minimum((length - x) / 0.04, 1)
            if instrument == "keys":
                envelope *= np.exp(-x * 2)
            mono[mask] += synth_note(x, note, instrument) * envelope
        return np.column_stack([mono, mono])

    @staticmethod
    def export_midi(content, target):
        import mido

        midi = mido.MidiFile(ticks_per_beat=480, charset="utf-8")
        conductor = mido.MidiTrack()
        conductor.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(content.bpm)))
        conductor.append(mido.MetaMessage("time_signature", numerator=4, denominator=4))
        if content.key:
            tonic, mode = content.key.split()
            # The key signature format permits Eb/Bb/Ab and F#/C# minor.
            major_alias = {"C#": "Db", "F#": "Gb", "Ab": "Ab"}
            minor_alias = {"Eb": "D#", "Ab": "G#", "Bb": "Bb"}
            tonic = (minor_alias if mode == "minor" else major_alias).get(tonic, tonic)
            conductor.append(
                mido.MetaMessage("key_signature", key=tonic + ("m" if mode == "minor" else ""))
            )
        previous = 0
        for marker in sorted(content.sections, key=lambda s: s.start):
            tick = round(marker.start * 480)
            conductor.append(mido.MetaMessage("marker", text=marker.name, time=tick - previous))
            previous = tick
        midi.tracks.append(conductor)
        instrument_index = 0
        for track in content.tracks:
            if track.kind != "midi":
                continue
            events, part = [], mido.MidiTrack()
            part.append(mido.MetaMessage("track_name", name=track.name))
            part.append(mido.MetaMessage("midi_port", port=instrument_index // 15))
            channel = instrument_index % 15
            if channel >= 9:
                channel += 1
            if track.instrument == "vcsl-drums":
                channel = 9
            else:
                program = {"vcsl-piano": 0, "vcsl-marimba": 12, "keys": 4, "bass": 33, "pad": 88}[
                    track.instrument
                ]
                part.append(mido.Message("program_change", program=program, channel=channel))
            instrument_index += 1
            for clip in track.clips:
                for note in clip.notes:
                    at = note.start * 60 / content.bpm - clip.offset
                    stop = min(clip.duration, at + note.length * 60 / content.bpm)
                    at = max(0, at)
                    if stop <= at:
                        continue
                    on, off = [(clip.start + s) * content.bpm / 60 * 480 for s in (at, stop)]
                    events.extend([(round(on), 1, note), (round(off), 0, note)])
            previous = 0
            for tick, on, note in sorted(events, key=lambda e: (e[0], e[1], e[2].pitch)):
                part.append(
                    mido.Message(
                        "note_on" if on else "note_off",
                        note=note.pitch,
                        velocity=note.velocity if on else 0,
                        channel=channel,
                        time=tick - previous,
                    )
                )
                previous = tick
            midi.tracks.append(part)
        if len(midi.tracks) == 1:
            raise StudioError("Add MIDI notes before exporting MIDI")
        midi.save(target)


class ArrangementRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def scoped(request):
            try:
                return await handler(request)
            except StudioError:
                raise
            except (ValueError, OSError) as error:
                raise HTTPException(422, str(error)) from error

        return scoped


def router(studio, manager):
    service = ArrangementService(studio, manager)
    from .audition import Compare
    from .creation import Adopt, CreationManager, Generate
    from .fitting import FitPreview

    creation = CreationManager(service)
    studio._creation_manager = creation
    api = APIRouter(prefix="/api/workstation", route_class=ArrangementRoute)

    @api.get("/generation/status")
    def generation_status():
        return creation.health()

    @api.get("/projects/{key}/generations")
    def generations(key: str):
        return creation.list(key)

    @api.post("/projects/{key}/generations", status_code=202)
    def generate(key: str, request: Generate):
        return creation.submit(key, request)

    @api.post("/projects/{key}/generation-preview")
    def generation_preview(key: str, request: Generate):
        return creation.preview(key, request)

    @api.post("/projects/{key}/generations/{identity}/cancel")
    def cancel_generation(key: str, identity: str):
        return creation.cancel(key, identity)

    @api.get("/projects/{key}/generations/{identity}/audio")
    def generated_audio(key: str, identity: str):
        return FileResponse(creation.audio(key, identity), media_type="audio/wav")

    @api.post("/projects/{key}/generations/{identity}/adopt")
    def adopt_generation(key: str, identity: str, request: Adopt):
        return creation.adopt(key, identity, request)

    @api.get("/library")
    def factory_library():
        return library.public()

    @api.get("/library/samples/{identity}")
    def factory_sample(identity: str):
        return FileResponse(
            library.sample_path(identity),
            media_type="audio/flac",
            headers={"Cache-Control": "private, max-age=86400"},
        )

    @api.post("/midi/inspect")
    def inspect_midi(file: UploadFile):
        return midi_import.summary(service.midi_bytes(file)[1])

    @api.get("/projects")
    def projects(deleted: bool = False):
        return service.list(deleted)

    @api.post("/projects", status_code=201)
    def create(request: Create):
        return service.create(request)

    @api.post("/projects/import-pack", status_code=201)
    def import_pack(file: UploadFile):
        from .project_pack import restore_pack

        return restore_pack(service, file)

    @api.post("/projects/{key}/pack")
    def pack(key: str, request: RevisionRequest):
        from .project_pack import export_pack

        return export_pack(service, key, request.revision)

    @api.get("/projects/{key}")
    def get(key: str):
        return service.get(key)

    @api.put("/projects/{key}")
    def save(key: str, request: Save):
        return service.update(key, request.revision, request.content)

    @api.post("/projects/{key}/history/{direction}")
    def history(key: str, direction: str, request: RevisionRequest):
        return service.history(key, request.revision, direction)

    @api.post("/projects/{key}/trash")
    def trash(key: str, request: RevisionRequest):
        return service.trash(key, request.revision)

    @api.post("/projects/{key}/restore")
    def restore(key: str, request: RevisionRequest):
        return service.trash(key, request.revision, True)

    @api.post("/projects/{key}/import")
    def import_file(
        key: str,
        revision: int,
        file: UploadFile,
        at: float = Query(default=0, ge=0, le=599, allow_inf_nan=False),
        import_id: str | None = Query(default=None, pattern=ID),
    ):
        return service.import_file(key, revision, file, at, import_id)

    @api.post("/projects/{key}/attach")
    def attach(key: str, request: Attach):
        return service.attach(key, request)

    @api.post("/projects/{key}/process", status_code=202)
    def process_clip(key: str, request: ProcessClip):
        return service.process_clip(key, request)

    @api.post("/projects/{key}/fit-preview")
    def fit_preview(key: str, request: FitPreview):
        return service.fit_preview(key, request)

    @api.post("/projects/{key}/comparisons")
    def comparison(key: str, request: Compare):
        from .audition import prepare

        return prepare(service, creation, key, request)

    @api.get("/projects/{key}/comparisons/{identity}/{side}")
    def comparison_audio(key: str, identity: str, side: str):
        from .audition import audio as comparison_path

        return FileResponse(comparison_path(service, key, identity, side), media_type="audio/wav")

    @api.get("/projects/{key}/processing")
    def processing(key: str):
        return service.processing(key)

    @api.post("/projects/{key}/processing/{task}/adopt-stems")
    def adopt_stems(key: str, task: str, request: RevisionRequest):
        return service.adopt_stems(key, task, request.revision)

    @api.post("/projects/{key}/processing/{task}/adopt-melody")
    def adopt_melody(key: str, task: str, request: RevisionRequest):
        return service.adopt_melody(key, task, request.revision)

    @api.post("/projects/{key}/patterns")
    def add_pattern(key: str, request: PatternRequest):
        return service.add_pattern(key, request)

    @api.post("/projects/{key}/midi")
    def import_midi(
        key: str, revision: int, file: UploadFile, at: float = 0, use_source_tempo: bool = False
    ):
        return service.import_midi(key, revision, file, at, use_source_tempo)

    @api.get("/projects/{key}/credits")
    def credits(key: str):
        from fastapi.responses import Response

        return Response(
            service.credits(key),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="music-workbench-credits.txt"'},
        )

    @api.get("/projects/{key}/audio/{asset}")
    def audio(key: str, asset: str):
        return FileResponse(service.asset_path(key, asset), media_type="audio/wav")

    @api.post("/projects/{key}/export/{kind}")
    def export(key: str, kind: str, request: RevisionRequest):
        return service.export(key, request.revision, kind)

    @api.get("/exports/{filename}")
    def download(filename: str):
        if not re.fullmatch(r"[a-f0-9]{16}\.(wav|mid|mwb)", filename):
            raise HTTPException(404)
        path = studio.safe_file(studio.root, ".arrangement-exports/" + filename)
        return FileResponse(path, filename="music-workbench-" + filename)

    return api
