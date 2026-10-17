"""Persistent, serial local capability queue shared by UI, MCP and Codex."""

import json
import os
import re
import shutil
import threading
import time
import uuid

from filelock import FileLock, Timeout

from ..io import fingerprint, read_json, sha256, write_json
from ..lyric_models import MODELS
from . import dsp
from .process import TaskStopped, log_tail, run_owned
from .registry import ModelRegistry, child_environment
from .service import StudioError
from .task_range import stable_wav_header
from .warm_worker import IDLE_SECONDS, REUSABLE, WarmWorker

PENDING = ("queued", "checking", "running", "cancelling")


class TaskManager:
    def __init__(self, service, settings=None):
        self.service = service
        self.registry = ModelRegistry(service, settings)
        self.stopping = threading.Event()
        self.wake = threading.Event()
        self.worker = None
        self.worker_input = None
        self.thread = threading.Thread(target=self._pump, daemon=True, name="studio-local-tasks")
        lock = service.root / ".studio-tasks.lock"
        if lock.is_symlink():
            raise StudioError("Invalid task queue lock")
        self.lock = FileLock(str(lock), timeout=0)
        self.thread.start()

    def _decode(self, row):
        return {**json.loads(row["data"]), "status": row["status"]}

    def get(self, project, task):
        self.service.project_dir(project)
        with self.service.connection() as db:
            row = db.execute(
                "SELECT * FROM tasks WHERE project=? AND id=?", (project, task)
            ).fetchone()
        if row is None:
            raise StudioError("Task does not exist", 404)
        return self._decode(row)

    def list(self, project):
        self.service.project_dir(project)
        with self.service.connection() as db:
            return [
                self._decode(row)
                for row in db.execute(
                    "SELECT * FROM tasks WHERE project=? ORDER BY created DESC LIMIT 100",
                    (project,),
                )
            ]

    def busy(self, project):
        with self.service.connection() as db:
            return (
                db.execute(
                    "SELECT 1 FROM tasks WHERE project=? AND status IN "
                    "('queued','checking','running','cancelling') LIMIT 1",
                    (project,),
                ).fetchone()
                is not None
            )

    def submit(self, project, request, actor="ui"):
        if self.stopping.is_set():
            raise StudioError("Task queue is closing", 503)
        spec = self.registry.spec(request.model)
        if request.alignment != "auto" and request.model != "qwen3-asr":
            raise StudioError("Independent Qwen timing is only available with the Qwen tool")
        if spec["stage"] != "transform" and (request.time_ratio != 1 or request.pitch_shift != 0):
            raise StudioError("Time/pitch parameters require the time-pitch capability")
        if spec["stage"] != "denoise" and request.strength != 1:
            raise StudioError("Cleanup strength is only supported by speech cleanup models")
        if spec.get("device") == "cpu" and request.device == "cuda":
            raise StudioError("This capability uses CPU; choose CPU or Auto")
        # The guarded snapshot is independent of subsequent edits or selected analysis versions.
        with self.service.project_guard(project):
            with self.service.transaction() as db:
                row, state = self.service._row(db, project)
                self.service._check_revision(row, request.revision)
                asset = state["active"] if request.asset == "current" else request.asset
                count = db.execute(
                    "SELECT COUNT(*) FROM tasks WHERE status IN "
                    "('queued','checking','running','cancelling')"
                ).fetchone()[0]
                if count >= 20:
                    raise StudioError(
                        "The queue has 20 pending tasks; finish or cancel some first", 409
                    )
            source = self.service.asset_path(project, asset)
            import soundfile as sf

            info = sf.info(source)
            first, last = 0, info.frames
            if request.range is not None:
                first = round(request.range.start * info.samplerate)
                last = round(request.range.end * info.samplerate)
                if first >= info.frames or last > info.frames + 1 or last <= first:
                    raise StudioError("Processing range is outside the source audio")
                last = min(last, info.frames)
            duration = (last - first) / info.samplerate
            if spec["stage"] == "transform" and duration / request.time_ratio > 600:
                raise StudioError("Transformed source would exceed the 10-minute limit")
            limit = self.registry.describe(request.model)["max_duration_seconds"]
            if duration > limit:
                raise StudioError(
                    f"This capability supports {limit}s per task; trim a shorter clip first"
                )
            key = uuid.uuid4().hex[:16]
            directory = self.service.studio_dir(project, f"tasks/{key}")
            required_bytes = (last - first) * info.channels * 4 * 4 + 128 * 1024**2
            if shutil.disk_usage(directory).free < required_bytes:
                raise StudioError("Insufficient free disk space for a pinned input and outputs")
            source_hash = sha256(source)
            snapshot = directory / "input.wav"
            if request.range is None:
                shutil.copyfile(source, snapshot)
            else:
                with (
                    sf.SoundFile(source) as audio,
                    sf.SoundFile(
                        snapshot,
                        "w",
                        samplerate=info.samplerate,
                        channels=info.channels,
                        subtype="FLOAT",
                    ) as pinned,
                ):
                    audio.seek(first)
                    remaining = last - first
                    while remaining:
                        block = audio.read(min(65536, remaining), dtype="float32", always_2d=True)
                        if not len(block):
                            raise StudioError("Input changed while pinning its range", 409)
                        pinned.write(block)
                        remaining -= len(block)
                stable_wav_header(snapshot)
            input_hash = sha256(snapshot)
            if (request.range is None and input_hash != source_hash) or sha256(
                source
            ) != source_hash:
                raise StudioError("Input changed while creating a task; try again", 409)
            source_range = {
                "scope": "clip" if request.range is not None else "asset",
                "start_frame": first,
                "end_frame": last,
                "sample_rate": info.samplerate,
                "start": first / info.samplerate,
                "end": last / info.samplerate,
                "source_frames": info.frames,
                "source_sha256": source_hash,
            }
            config = self.registry.settings.model_dump()
            device = self.registry.settings.device if request.device == "auto" else request.device
            if spec.get("device") == "cpu":
                device = "cpu"
            config.update(
                device=device,
                offline=True,
                asr_backend="whisper",
                asr_model="small",
                asr_revision="536b0662742c02347bc0e980a01041f333bce120",
                rhythm_backend="librosa_percussive",
                separation_model="htdemucs",
                four_stems=request.model == "demucs-four-stems",
                pitch_backend="crepe",
                lyrics_alignment=request.alignment if request.model == "qwen3-asr" else "native",
                language=request.language,
                cleanup_strength=request.strength,
                time_ratio=request.time_ratio,
                pitch_shift=request.pitch_shift,
                note_onset=request.note_onset,
                note_frame=request.note_frame,
                note_min_ms=request.note_min_ms,
            )
            if request.model == "qwen3-asr":
                config.update(
                    asr_backend="qwen", asr_model=MODELS["qwen"][0], asr_revision=MODELS["qwen"][1]
                )
            data = {
                "id": key,
                "project": project,
                "model": request.model,
                "stage": spec["stage"],
                "revision": request.revision,
                "source_asset": asset,
                "input_sha256": input_hash,
                "source_range": source_range,
                "actor": actor,
                "created_at": time.time(),
                "device": device,
                "alignment": request.alignment,
                "strength": request.strength if spec["stage"] == "denoise" else None,
                "note_settings": {
                    "note_onset": request.note_onset,
                    "note_frame": request.note_frame,
                    "note_min_ms": request.note_min_ms,
                }
                if request.model == "basic-pitch"
                else None,
                "time_ratio": request.time_ratio,
                "pitch_shift": request.pitch_shift,
                "input_audio": dsp.inspect_audio(snapshot),
                "artifacts": [],
                "error": None,
            }
            write_json(
                directory / "request.json",
                {
                    "model": request.model,
                    "stage": spec["stage"],
                    "input": str(snapshot),
                    "input_sha256": input_hash,
                    "source_range": source_range,
                    "output": str(directory / "output"),
                    "settings": config,
                    "owner_pid": os.getpid(),
                },
            )
            with self.service.transaction() as db:
                row, _ = self.service._row(db, project)
                self.service._check_revision(row, request.revision)
                count = db.execute(
                    "SELECT COUNT(*) FROM tasks WHERE status IN "
                    "('queued','checking','running','cancelling')"
                ).fetchone()[0]
                if count >= 20:
                    raise StudioError("The queue has 20 pending tasks; cancel some first", 409)
                db.execute(
                    "INSERT INTO tasks VALUES (?,?,?,?,?)",
                    (key, project, "queued", json.dumps(data), data["created_at"]),
                )
                self.service._event(
                    db, project, actor, "task.queued", {"task": key, "model": request.model}
                )
        self.wake.set()
        return {**data, "status": "queued"}

    def cancel(self, project, task, actor="ui"):
        self.get(project, task)
        with self.service.transaction() as db:
            row = db.execute(
                "SELECT * FROM tasks WHERE project=? AND id=?", (project, task)
            ).fetchone()
            if row["status"] in PENDING:
                status = "cancelled" if row["status"] == "queued" else "cancelling"
                data = json.loads(row["data"])
                data["cancel_requested_at"] = time.time()
                db.execute(
                    "UPDATE tasks SET status=?,data=? WHERE id=?", (status, json.dumps(data), task)
                )
                self.service._event(db, project, actor, f"task.{status}", {"task": task})
        self.wake.set()
        return self.get(project, task)

    def _status(self, task, status, **changes):
        with self.service.transaction() as db:
            row = db.execute("SELECT * FROM tasks WHERE id=?", (task,)).fetchone()
            if status in ("checking", "running") and row["status"] in ("cancelling", "cancelled"):
                raise TaskStopped("Task cancelled before starting")
            data = json.loads(row["data"])
            data.update(changes)
            db.execute(
                "UPDATE tasks SET status=?,data=? WHERE id=?", (status, json.dumps(data), task)
            )
            self.service._event(
                db,
                data["project"],
                "system",
                f"task.{status}",
                {"task": task, "model": data["model"]},
            )
        return {**data, "status": status}

    def _cancelled(self, task):
        if self.stopping.is_set():
            return True
        with self.service.connection() as db:
            row = db.execute("SELECT status FROM tasks WHERE id=?", (task,)).fetchone()
        return row is None or row["status"] in ("cancelling", "cancelled")

    def _recover(self):
        # Holding the cross-process lock proves no other queue worker owns these rows.
        with self.service.connection() as db:
            rows = list(
                db.execute(
                    "SELECT id FROM tasks WHERE status IN ('checking','running','cancelling')"
                )
            )
        for row in rows:
            self._status(
                row["id"],
                "interrupted",
                finished_at=time.time(),
                error="Previous task owner stopped. Run a new task; original audio is retained.",
            )

    def _run(self, task):
        key, project = task["id"], task["project"]
        invocation_started = time.monotonic()
        try:
            self.service.project_dir(project)
            self._status(key, "checking", started_at=time.time())
            directory = self.service.studio_dir(project, f"tasks/{key}")
            request_file = directory / "request.json"
            request = read_json(request_file)
            input_identity = fingerprint({"model": task["model"], "settings": request["settings"]})
            if self.worker_input != input_identity or (
                self.worker and self.worker.process.poll() is not None
            ):
                self._retire_worker()
            spec = self.registry.require(
                task["model"], cancelled=lambda: self._cancelled(key), device=task["device"]
            )
            if self._cancelled(key):
                raise TaskStopped("Task cancelled")
            request["settings"].update(
                self.registry.environment_settings(task["model"], task["device"])
            )
            request["owner_pid"] = os.getpid()
            write_json(request_file, request)
            self._status(
                key,
                "running",
                runtime=self.registry.describe(task["model"], device=task["device"])["health"],
            )
            python = self.registry.python(spec, task["device"])
            environment = child_environment(request["settings"]["model_dir"])
            identity = fingerprint(
                {"model": task["model"], "python": python, "settings": request["settings"]}
            )
            if self.worker and self.worker.identity != identity:
                self._retire_worker()
            # The base runtime remains a one-shot subprocess (including test/tool fixtures).
            if task["model"] in REUSABLE and spec["runtime"] != "base":
                if not self.worker:
                    self.worker = WarmWorker(python, environment, directory, identity)
                    self.worker_input = input_identity
                code = self.worker.run(request_file, cancelled=lambda: self._cancelled(key))
            else:
                code = run_owned(
                    [
                        python,
                        "-X",
                        "utf8",
                        "-m",
                        "music_studio.studio.task_worker",
                        str(request_file),
                    ],
                    directory / "worker.log",
                    environment,
                    cancelled=lambda: self._cancelled(key),
                )
            if code:
                raise StudioError(
                    f"Local model exited {code}. " + log_tail(directory / "worker.log")
                )
            if self._cancelled(key):
                raise TaskStopped("Task cancelled")
            result = read_json(directory / "output/result.json")
            result["metrics"]["invocation_seconds"] = round(
                time.monotonic() - invocation_started, 3
            )
            folder = self.service.project_dir(project)
            artifacts = []
            if task["stage"] == "denoise":
                snapshot = directory / "input.wav"
                if sha256(snapshot) != task["input_sha256"]:
                    raise StudioError("Pinned comparison input changed")
                artifacts.append(
                    {
                        "role": "cleanup-input",
                        "kind": "audio",
                        "mime": "audio/wav",
                        "id": uuid.uuid4().hex[:16],
                        "task": key,
                        "model": task["model"],
                        "file": str(snapshot.relative_to(folder)),
                        "sha256": task["input_sha256"],
                        "input_sha256": task["input_sha256"],
                        "audio": task["input_audio"],
                    }
                )
            for artifact in result["artifacts"]:
                file = self.service.safe_file(directory / "output", artifact["file"])
                record = {
                    **artifact,
                    "id": uuid.uuid4().hex[:16],
                    "task": key,
                    "model": task["model"],
                    "file": str(file.relative_to(folder)),
                    "sha256": sha256(file),
                    "input_sha256": task["input_sha256"],
                }
                if record["kind"] == "audio":
                    record["audio"] = dsp.inspect_audio(file)
                    expected = dict(task["input_audio"])
                    if task["stage"] == "transform":
                        expected["frames"] = round(expected["frames"] / task["time_ratio"])
                    if any(
                        record["audio"][field] != expected[field]
                        for field in ("frames", "sample_rate", "channels")
                    ):
                        raise StudioError(
                            "Model changed the audio timeline; refusing mismatched output"
                        )
                artifacts.append(record)
            # One transaction publishes all outputs, never partial artifacts or an auto-adopt.
            with self.service.transaction() as db:
                row = db.execute("SELECT * FROM tasks WHERE id=?", (key,)).fetchone()
                if row["status"] == "cancelling" or self.stopping.is_set():
                    raise TaskStopped("Task cancelled")
                for record in artifacts:
                    db.execute(
                        "INSERT INTO assets VALUES (?,?,?,?,?,?)",
                        (
                            record["id"],
                            project,
                            key,
                            record["role"],
                            record["kind"],
                            json.dumps(record),
                        ),
                    )
                data = json.loads(row["data"])
                data.update(
                    artifacts=[{k: v for k, v in a.items() if k != "file"} for a in artifacts],
                    metrics=result["metrics"],
                    finished_at=time.time(),
                )
                db.execute(
                    "UPDATE tasks SET status='complete',data=? WHERE id=?", (json.dumps(data), key)
                )
                self.service._event(
                    db,
                    project,
                    "system",
                    "task.complete",
                    {"task": key, "model": task["model"], "assets": [a["id"] for a in artifacts]},
                )
        except TaskStopped:
            self._retire_worker()
            self._status(
                key,
                "interrupted" if self.stopping.is_set() else "cancelled",
                finished_at=time.time(),
            )
        except Exception as error:
            self._retire_worker()
            self._status(
                key,
                "cancelled" if self._cancelled(key) else "failed",
                error=str(error),
                finished_at=time.time(),
            )

    def _retire_worker(self):
        if self.worker:
            self.worker.close()
            self.worker = None
        self.worker_input = None

    def _generation_waiting(self):
        with self.service.connection() as db:
            exists = db.execute(
                "SELECT 1 FROM sqlite_master WHERE name='creation_tasks'"
            ).fetchone()
            return bool(
                exists
                and db.execute(
                    "SELECT 1 FROM creation_tasks WHERE status='queued' LIMIT 1"
                ).fetchone()
            )

    def _pump(self):
        while not self.stopping.is_set():
            try:
                with self.lock:
                    try:
                        self._recover()
                        while not self.stopping.is_set():
                            # Release GPU memory and the shared lock before ACE-Step starts.
                            if self.worker and self._generation_waiting():
                                break
                            with self.service.connection() as db:
                                row = db.execute(
                                    "SELECT * FROM tasks WHERE status='queued' "
                                    "ORDER BY created LIMIT 1"
                                ).fetchone()
                            if row is None:
                                if (
                                    not self.worker
                                    or time.monotonic() - self.worker.last_used >= IDLE_SECONDS
                                ):
                                    break
                                self.wake.wait(0.2)
                                self.wake.clear()
                                continue
                            self._run(self._decode(row))
                    finally:
                        self._retire_worker()
            except Timeout:
                pass
            except Exception:
                # Preserve the durable queue if an OS/SQLite operation is transiently unavailable.
                pass
            self.wake.wait(0.4)
            self.wake.clear()

    def artifact_path(self, project, asset):
        if not re.fullmatch(r"[a-f0-9]{16}", asset):
            raise StudioError("Asset does not exist", 404)
        folder = self.service.project_dir(project)
        with self.service.connection() as db:
            row = db.execute(
                "SELECT data FROM assets WHERE project=? AND id=?", (project, asset)
            ).fetchone()
        if row is None:
            raise StudioError("Asset does not exist", 404)
        record = json.loads(row["data"])
        return self.service.safe_file(folder, record["file"]), record

    def input_path(self, project, identity):
        task = self.get(project, identity)
        directory = self.service.studio_dir(project, f"tasks/{task['id']}")
        path = self.service.safe_file(directory, "input.wav")
        if sha256(path) != task["input_sha256"]:
            raise StudioError("Pinned task input changed", 409)
        return path

    def close(self):
        self.stopping.set()
        self.wake.set()
        self.thread.join(timeout=20)
