"""Durable generation drafts; adoption is an explicit, reversible arrangement edit."""

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Literal

from filelock import FileLock, Timeout
from pydantic import Field, model_validator

from ..io import read_json, sha256, write_json
from . import dsp
from .arrangement import Attach, Origin, uid
from .composition import ContextRequest, compile_context
from .models import RevisionRequest
from .process import TaskStopped, log_tail, run_owned
from .registry import child_environment
from .service import StudioError

SOURCE_REVISION = "ca1e85fe9430179831e6bc6be790c332190a3866"
MODEL_REVISION = "19671f406d603126926c1b7e2adc169acbcade22"
COMPONENTS = (
    "acestep-v15-turbo/model.safetensors",
    "vae/diffusion_pytorch_model.safetensors",
    "Qwen3-Embedding-0.6B/model.safetensors",
)
PENDING = ("queued", "checking", "running", "cancelling")


class Generate(RevisionRequest, ContextRequest):
    prompt: str = Field(min_length=3, max_length=1200)
    lyrics: str = Field(default="", max_length=4000)
    instrumental: bool = True
    duration: int = Field(default=20, ge=10, le=60)
    bpm: int = Field(default=108, ge=30, le=300)
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
    steps: int = Field(default=8, ge=1, le=16)
    language: str = Field(default="unknown", pattern=r"^(unknown|zh|en|ja|ko)$")
    key: str = Field(default="", max_length=30)
    mode: Literal["text2music", "cover", "repaint"] = "text2music"
    source_clip: str | None = Field(default=None, pattern=r"^[a-f0-9]{16}$")
    reference_strength: float = Field(default=0.65, ge=0, le=1)
    repaint_start: float = Field(default=0, ge=0, le=59.5)
    repaint_end: float = Field(default=4, ge=0.5, le=60)
    repaint_blend: float = Field(default=0.1, ge=0, le=0.25)

    @model_validator(mode="after")
    def validate_text(self):
        self.prompt = self.prompt.strip()
        if len(self.prompt) < 3 or (not self.instrumental and not self.lyrics.strip()):
            raise ValueError("Describe the music; vocal drafts also need lyrics")
        if (self.mode != "text2music") != (self.source_clip is not None):
            raise ValueError("Audio variation requires a selected source clip")
        if self.mode == "repaint" and self.repaint_end - self.repaint_start < 0.5:
            raise ValueError("Select at least half a second to repaint")
        return self


class Adopt(RevisionRequest):
    at: float = Field(default=0, ge=0, le=599)
    target_section: bool = False
    replace_source: bool = False


def runtime():
    from .ai_setup import config_path

    path = config_path()
    if not path.is_file():
        raise StudioError(
            "Local AI is not installed. Open AI setup from Home to install it.",
            503,
        )
    config = read_json(path)
    if not isinstance(config, dict) or any(
        not isinstance(config.get(key), str) or not config[key]
        for key in ("python", "source", "checkpoints", "source_revision", "model_revision")
    ):
        raise StudioError("Invalid ACE-Step configuration; rerun python scripts/setup_ace.py", 503)
    if (
        config.get("source_revision") != SOURCE_REVISION
        or config.get("model_revision") != MODEL_REVISION
    ):
        raise StudioError("Unsupported ACE-Step revision; run the pinned setup script", 503)
    if (
        not Path(config["python"]).is_file()
        or not (Path(config["source"]) / "acestep/handler.py").is_file()
    ):
        raise StudioError("ACE-Step runtime is missing; rerun python scripts/setup_ace.py", 503)
    missing = [p for p in COMPONENTS if not (Path(config["checkpoints"]) / p).is_file()]
    if missing:
        raise StudioError("Missing ACE-Step weights: " + ", ".join(missing), 503)
    manifest = Path(config["checkpoints"]) / "music-studio-manifest.json"
    if not manifest.is_file() or sha256(manifest) != config.get("weights_manifest_sha256"):
        raise StudioError("Verify ACE-Step checkpoints with python scripts/setup_ace.py", 503)
    return config


class CreationManager:
    def __init__(self, arrangement):
        self.arrangement = arrangement
        self.studio = arrangement.studio
        self.stopping = threading.Event()
        self.wake = threading.Event()
        with self.studio.connection() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS creation_tasks (
                id TEXT PRIMARY KEY, project TEXT NOT NULL, status TEXT NOT NULL,
                data TEXT NOT NULL, created REAL NOT NULL
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS creation_project ON creation_tasks(project)")
        lock = self.studio.root / ".studio-tasks.lock"
        if lock.is_symlink():
            raise StudioError("Invalid task queue lock")
        self.lock = FileLock(str(lock), timeout=0)
        self.thread = threading.Thread(target=self._pump, daemon=True, name="studio-creation")
        self.thread.start()

    @staticmethod
    def health():
        try:
            config = runtime()
            return {
                "available": True,
                "state": "configured",
                "model_revision": config["model_revision"],
                "profile": "CUDA · INT8 weights · CPU offload · no LM · 10–60s drafts",
            }
        except (StudioError, OSError, ValueError, KeyError) as error:
            return {"available": False, "state": "unavailable", "message": str(error)}

    def directory(self, identity):
        if not re.fullmatch(r"[a-f0-9]{16}", identity):
            raise StudioError("Generation does not exist", 404)
        root = self.studio.root / ".creation-tasks"
        path = root / identity
        if root.is_symlink() or path.is_symlink():
            raise StudioError("Invalid creation task directory")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _public(self, row):
        data = json.loads(row["data"])
        data.pop("runtime", None)
        data["status"] = row["status"]
        if data["status"] == "running":
            try:
                data["progress"] = read_json(self.directory(row["id"]) / "output/progress.json")
            except (OSError, ValueError):
                pass
        return data

    def list(self, project):
        self.arrangement.get(project)
        with self.studio.connection() as db:
            return [
                self._public(r)
                for r in db.execute(
                    "SELECT * FROM creation_tasks WHERE project=? ORDER BY created DESC LIMIT 100",
                    (project,),
                )
            ]

    def get(self, project, identity):
        self.arrangement.get(project)
        with self.studio.connection() as db:
            row = db.execute(
                "SELECT * FROM creation_tasks WHERE project=? AND id=?", (project, identity)
            ).fetchone()
        if row is None:
            raise StudioError("Generation does not exist", 404)
        return self._public(row)

    def submit(self, project, request):
        if self.stopping.is_set():
            raise StudioError("Creation queue is closing", 503)
        config = runtime()
        key, now = uid(), time.time()
        data = {
            "id": key,
            "project": project,
            "kind": "generation",
            "model": "ACE-Step 1.5 Turbo",
            "base_revision": request.revision,
            "parameters": request.model_dump(exclude={"revision"}),
            "runtime": config,
            "created_at": now,
            "artifacts": [],
            "error": None,
            "model_revision": MODEL_REVISION,
            "source_revision": SOURCE_REVISION,
            "profile": config.get("profile", "bf16-offload"),
            "worker_sha256": sha256(Path(__file__).with_name("ace_worker.py")),
        }
        state = self.arrangement.get(project)
        if state["revision"] != request.revision:
            raise StudioError("Session changed; save before generating", 409)
        compiled = compile_context(state, request.prompt, request)
        if compiled["context"]:
            data["user_prompt"] = request.prompt
            data["composition_context"] = compiled["context"]
            data["parameters"]["prompt"] = compiled["prompt"]
            # Context has one authoritative tempo/key, identical to the pinned project.
            data["parameters"]["bpm"] = round(state["content"]["bpm"])
            data["parameters"]["key"] = state["content"].get("key", "")
        if request.mode != "text2music":
            import soundfile as sf

            clip = next(
                (
                    c
                    for t in state["content"]["tracks"]
                    for c in t["clips"]
                    if c["id"] == request.source_clip and c["asset"]
                ),
                None,
            )
            if not clip or not 10 <= clip["duration"] <= 60:
                raise StudioError("Select a 10–60 second audio clip for variation")
            if request.mode == "repaint" and request.repaint_end > clip["duration"]:
                raise StudioError("Repaint region exceeds the selected clip")
            path = self.arrangement.asset_path(project, clip["asset"])
            target = self.directory(key) / "reference.wav"
            with sf.SoundFile(path) as source:
                source.seek(round(clip["offset"] * source.samplerate))
                audio = source.read(
                    round(clip["duration"] * source.samplerate), dtype="float32", always_2d=True
                )
                sf.write(target, audio, source.samplerate, subtype="FLOAT")
            data["reference"] = {
                "sha256": sha256(target),
                "clip": clip,
                "source_sha256": sha256(path),
            }
            data["parameters"]["duration"] = round(clip["duration"])
        with self.studio.transaction() as db:
            row = self.arrangement.row(db, project)
            self.studio._check_revision(row, request.revision)
            count = db.execute(
                "SELECT COUNT(*) FROM creation_tasks WHERE status IN "
                "('queued','checking','running','cancelling')"
            ).fetchone()[0]
            if count >= 5:
                raise StudioError(
                    "Finish or cancel some creation drafts first (queue limit: 5)", 409
                )
            write_json(self.directory(key) / "request.json", data)
            db.execute(
                "INSERT INTO creation_tasks VALUES (?,?,?,?,?)",
                (key, project, "queued", json.dumps(data), now),
            )
        self.wake.set()
        return self.get(project, key)

    def preview(self, project, request):
        state = self.arrangement.get(project)
        if state["revision"] != request.revision:
            raise StudioError("Session changed; save before previewing", 409)
        compiled = compile_context(state, request.prompt, request)
        duration = request.duration
        if request.mode != "text2music":
            clip = next(
                (c for t in state["content"]["tracks"] for c in t["clips"]
                 if c["id"] == request.source_clip and c["asset"]), None
            )
            if not clip or not 10 <= clip["duration"] <= 60:
                raise StudioError("Select a 10–60 second audio clip for variation")
            duration = round(clip["duration"])
            if request.mode == "repaint" and request.repaint_end > clip["duration"]:
                raise StudioError("Repaint region exceeds the selected clip")
        return {
            **compiled,
            "bpm": round(state["content"]["bpm"]) if request.use_blueprint else request.bpm,
            "key": state["content"].get("key", "") if request.use_blueprint else request.key,
            "duration": duration,
        }

    def _status(self, identity, status, **changes):
        with self.studio.transaction() as db:
            row = db.execute("SELECT * FROM creation_tasks WHERE id=?", (identity,)).fetchone()
            if status in ("checking", "running", "complete") and row["status"] in (
                "cancelling",
                "cancelled",
            ):
                raise TaskStopped("Generation cancelled")
            data = json.loads(row["data"])
            data.update(changes)
            db.execute(
                "UPDATE creation_tasks SET status=?,data=? WHERE id=?",
                (status, json.dumps(data), identity),
            )

    def cancel(self, project, identity):
        self.get(project, identity)
        with self.studio.transaction() as db:
            row = db.execute("SELECT * FROM creation_tasks WHERE id=?", (identity,)).fetchone()
            if row["status"] in PENDING:
                db.execute(
                    "UPDATE creation_tasks SET status=? WHERE id=?",
                    ("cancelled" if row["status"] == "queued" else "cancelling", identity),
                )
        self.wake.set()
        return self.get(project, identity)

    def cancelled(self, identity):
        if self.stopping.is_set():
            return True
        with self.studio.connection() as db:
            row = db.execute("SELECT status FROM creation_tasks WHERE id=?", (identity,)).fetchone()
        return row is None or row["status"] in ("cancelling", "cancelled")

    def _run(self, task):
        key = task["id"]
        directory = self.directory(key)
        try:
            self.arrangement.get(task["project"])
            self._status(key, "checking", started_at=time.time())
            if task.get("worker_sha256") and task["worker_sha256"] != sha256(
                Path(__file__).with_name("ace_worker.py")
            ):
                raise StudioError("Generation backend changed while queued; submit a new draft")
            config = task["runtime"]
            worker = {**task, "output": str(directory / "output"), "owner_pid": os.getpid()}
            if task.get("reference"):
                reference = self.studio.safe_file(directory, "reference.wav")
                if sha256(reference) != task["reference"]["sha256"]:
                    raise StudioError("Pinned reference audio checksum changed")
                worker["reference_audio"] = str(reference)
            write_json(directory / "worker.json", worker)
            self._status(key, "running")
            arguments = [config["python"], "-X", "utf8", "-m",
                         "music_studio.studio.ace_worker", str(directory / "worker.json")]
            if config.get("managed"):
                # Use the current app's worker after an app upgrade, while keeping
                # sys.path in the isolated AI environment for all dependencies.
                arguments = [config["python"], "-X", "utf8", "-c",
                             "import music_studio,runpy,sys;"
                             "music_studio.__path__=[sys.argv.pop(1)];"
                             "runpy.run_module('music_studio.studio.ace_worker',run_name='__main__')",
                             str(Path(__file__).resolve().parents[1]),
                             str(directory / "worker.json")]
            code = run_owned(
                arguments,
                directory / "worker.log",
                child_environment(config["checkpoints"]),
                cancelled=lambda: self.cancelled(key),
                timeout=1800,
            )
            if code:
                raise StudioError(f"ACE-Step exited {code}. " + log_tail(directory / "worker.log"))
            if self.cancelled(key):
                raise TaskStopped("Generation cancelled")
            result = read_json(directory / "output/result.json")
            generated = self.studio.safe_file(directory / "output", result["file"])
            if task["parameters"].get("mode") == "repaint":
                from .repaint import splice

                options = task["parameters"]
                spliced = directory / "output/repaint-spliced.wav"
                result["metrics"]["repaint"] = splice(
                    directory / "reference.wav", generated, spliced,
                    options["repaint_start"], options["repaint_end"], options["repaint_blend"],
                )
                generated = spliced
            info = dsp.inspect_audio(generated)
            if not 1 <= info["duration"] <= 70:
                raise StudioError("Generation duration is outside the supported draft range")
            with generated.open("rb") as stream:
                source = self.arrangement.import_stream(
                    f"ACE-Step · Seed {task['parameters']['seed']}.wav", stream
                )
            canonical = self.studio.asset_path(source["id"], "source")
            self._status(
                key,
                "complete",
                source_project=source["id"],
                sha256=sha256(canonical),
                audio=dsp.inspect_audio(canonical),
                metrics=result["metrics"],
                finished_at=time.time(),
            )
        except TaskStopped:
            self._status(
                key,
                "interrupted" if self.stopping.is_set() else "cancelled",
                finished_at=time.time(),
            )
        except Exception as error:
            changes = {}
            try:
                failure = read_json(directory / "output/failure.json")
                if isinstance(failure.get("metrics"), dict):
                    changes["metrics"] = failure["metrics"]
            except (OSError, ValueError, AttributeError):
                pass
            self._status(key, "failed", error=str(error), finished_at=time.time(), **changes)

    def _pump(self):
        while not self.stopping.is_set():
            try:
                with self.lock:
                    with self.studio.connection() as db:
                        interrupted = list(
                            db.execute(
                                "SELECT id FROM creation_tasks WHERE status IN "
                                "('checking','running','cancelling')"
                            )
                        )
                    for row in interrupted:
                        self._status(
                            row["id"],
                            "interrupted",
                            finished_at=time.time(),
                            error="Previous owner stopped. Project and earlier drafts are kept.",
                        )
                    with self.studio.connection() as db:
                        row = db.execute(
                            "SELECT * FROM creation_tasks WHERE status='queued' "
                            "ORDER BY created LIMIT 1"
                        ).fetchone()
                    if row is not None:
                        self._run(json.loads(row["data"]))
            except Timeout:
                pass
            except Exception:
                pass
            self.wake.wait(0.4)
            self.wake.clear()

    def audio(self, project, identity):
        task = self.get(project, identity)
        if task["status"] != "complete":
            raise StudioError("This draft is not ready", 409)
        path = self.studio.asset_path(task["source_project"], "source")
        if sha256(path) != task["sha256"]:
            raise StudioError("Generated draft checksum changed")
        return path

    def adopt(self, project, identity, request):
        task = self.get(project, identity)
        at = request.at
        if request.target_section:
            pinned = (task.get("composition_context") or {}).get("section")
            state = self.arrangement.get(project)
            current = next(
                (s for s in state["content"].get("sections", [])
                 if pinned and s["id"] == pinned["id"]), None
            )
            if (
                not current
                or any(current[k] != pinned[k] for k in ("start", "end"))
                or state["content"]["bpm"] != task["composition_context"]["bpm"]
            ):
                raise StudioError("Target section timing changed; add at the playhead instead", 409)
            at = current["start"] * 60 / state["content"]["bpm"]
        self.audio(project, identity)
        reference = task.get("reference")
        original = (reference or {}).get("clip", {}).get("origin") or {}
        details = (
            f"Model {MODEL_REVISION}; source {SOURCE_REVISION}; task {identity}. "
            + f"Profile {task.get('profile', 'bf16')}; worker {task.get('worker_sha256', '')}. "
        )
        if reference:
            details += (
                f"Reference SHA256 {reference['sha256']}; "
                f"original audio SHA256 {reference['source_sha256']}; "
                + "original attribution: "
                + json.dumps(original, ensure_ascii=False)[:1500]
                + ". "
            )
        if context := task.get("composition_context"):
            details += (
                f"Blueprint context SHA256 {context['sha256']}; "
                f"project {context['project']} revision {context['revision']}. "
            )
        details += json.dumps({k: v for k, v in task["parameters"].items() if k != "lyrics"})
        origin = Origin(
            title=f"ACE-Step 1.5 Turbo · Seed {task['parameters']['seed']}",
            author=("Generated locally with ACE-Step; " + original.get("author", ""))[:1000],
            license=("Model: MIT; reference: " + original.get("license", "unspecified")
                     if reference else "Model: MIT")[:150],
            source_url="https://github.com/ACE-Step/ACE-Step-1.5",
            sha256=task["sha256"], details=details[:3000],
        )
        if request.replace_source:
            if task["parameters"].get("mode") != "repaint" or not reference:
                raise StudioError("Only region repaint can replace its source clip")
            from ..io import fingerprint
            from .arrangement import Arrangement

            state = self.arrangement.get(project)
            content = Arrangement.model_validate(state["content"])
            clip = next((c for t in content.tracks for c in t.clips
                         if c.id == reference["clip"]["id"]), None)
            # Default-filled fields allow older project snapshots to compare correctly.
            from .arrangement import Clip

            if not clip or clip != Clip.model_validate(reference["clip"]):
                raise StudioError("Source clip changed; add this candidate on a new track", 409)
            audio = task["audio"]
            asset = {
                "id": fingerprint({"project": task["source_project"], "asset": "source"})[:16],
                "source_project": task["source_project"], "source_asset": "source",
                "name": "AI region repaint", "duration": audio["duration"],
                "waveform": dsp.peaks(self.audio(project, identity), 480),
            }
            clip.asset, clip.offset, clip.origin = asset["id"], 0, origin
            return self.arrangement.update(project, request.revision, content, asset)
        return self.arrangement.attach(
            project,
            Attach(
                revision=request.revision,
                source_project=task["source_project"],
                asset="source",
                at=at,
            ),
            origin=origin,
        )

    def close(self):
        self.stopping.set()
        self.wake.set()
        self.thread.join(timeout=20)
