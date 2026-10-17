"""One managed, resumable local AI installation, separate from projects and app files."""

import contextlib
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from filelock import FileLock, Timeout

from ..io import read_json, write_json
from .process import TaskStopped, log_tail, run_owned
from .service import StudioError

ACTIVE = ("installing", "cancelling")


def data_root():
    override = os.environ.get("MUSIC_WORKBENCH_DATA")
    if override:
        return Path(override).resolve()
    from platformdirs import user_data_path

    return user_data_path("MusicWorkbench", appauthor=False).resolve()


def config_path():
    explicit = os.environ.get("MUSIC_STUDIO_ACE_CONFIG")
    if explicit:
        return Path(explicit).resolve()
    developer = Path(".artifacts/acestep-runtime.json").resolve()
    return developer if developer.is_file() else data_root() / "AI/acestep-runtime.json"


def preflight(root):
    root.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(root).free
    gpu, error = [], None
    try:
        probe = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        for line in probe.stdout.strip().splitlines():
            name, memory, driver = [x.strip() for x in line.split(",")]
            gpu.append({"name": name, "memory_mib": int(float(memory)), "driver": driver})
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        error = type(exc).__name__
    supported = os.name == "nt" and platform.machine().lower() in ("amd64", "x86_64")
    reasons = []
    if not supported:
        reasons.append("windows-x64")
    if not any(g["memory_mib"] >= 8000 for g in gpu):
        reasons.append("nvidia-8gb")
    if free < 35 * 1024**3:
        reasons.append("disk-35gb")
    return {
        "supported": not reasons,
        "reasons": reasons,
        "gpus": gpu,
        "free_bytes": free,
        "required_free_bytes": 35 * 1024**3,
        "directory": str(root),
        "probe_error": error,
        "download_estimate": "8–12 GB",
        "license": "MIT",
        "source": "https://github.com/ace-step/ACE-Step-1.5",
    }


class AISetup:
    def __init__(self, root=None):
        self.root = (root or data_root() / "AI").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "setup.json"
        self.guard = threading.RLock()
        self.cancelled = threading.Event()
        self.thread = None
        self.lock = FileLock(str(self.root / "setup.lock"), timeout=0, thread_local=False)
        # A second window can observe the job. Only an unlocked, abandoned job is interrupted.
        try:
            with self.lock:
                record = self.status()
                if record["state"] in ACTIVE:
                    self._state(
                        "interrupted", error="The previous setup was interrupted. Retry to resume."
                    )
        except Timeout:
            pass

    def _state(self, state, **kwargs):
        write_json(self.path, {"state": state, "updated_at": time.time(), **kwargs})

    def status(self):
        try:
            result = read_json(self.path)
        except (OSError, ValueError):
            result = {"state": "idle"}
        progress = self.root / "progress.json"
        if result["state"] in ACTIVE and progress.is_file():
            with contextlib.suppress(OSError, ValueError):
                result["progress"] = read_json(progress)
        result["preview"] = (self.root / "verification/generated.wav").is_file()
        return result

    def start(self):
        with self.guard:
            if self.thread and self.thread.is_alive():
                return self.status()
            check = preflight(self.root)
            if not check["supported"]:
                raise StudioError("AI setup requirements: " + ", ".join(check["reasons"]), 422)
            # The lock is explicitly shared with our worker thread; other windows observe it.
            try:
                self.lock.acquire()
            except Timeout as exc:
                raise StudioError("AI setup is already running in another window", 409) from exc
            self.cancelled.clear()
            (self.root / "cancel.request").unlink(missing_ok=True)
            self._state("installing")
            write_json(self.root / "progress.json", {"stage": "preparing", "fraction": 0})
            self.thread = threading.Thread(target=self._run, daemon=True, name="ai-setup")
            self.thread.start()
            return self.status()

    def _run(self):
        try:
            try:
                env = os.environ.copy()
                env.update(PYTHONUTF8="1", PYTHONUNBUFFERED="1", PYTHONDONTWRITEBYTECODE="1")
                code = run_owned(
                    [
                        sys.executable,
                        "-X",
                        "utf8",
                        "-m",
                        "music_studio.studio.ai_install_worker",
                        "--root",
                        str(self.root),
                        "--owner-pid",
                        str(os.getpid()),
                    ],
                    self.root / "setup.log",
                    env,
                    cancelled=lambda: (
                        self.cancelled.is_set() or (self.root / "cancel.request").exists()
                    ),
                    timeout=14400,
                )
                if code:
                    raise RuntimeError(log_tail(self.root / "setup.log", 1800))
                self._state("ready")
            finally:
                self.lock.release()
        except Timeout:
            # Another process won the cross-window race; leave its job state intact.
            pass
        except TaskStopped:
            self._state("cancelled")
        except Exception as exc:
            self._state("failed", error=str(exc)[-2000:])

    def cancel(self):
        with self.guard:
            if self.status()["state"] in ACTIVE:
                (self.root / "cancel.request").touch()
                self.cancelled.set()
                self._state("cancelling")
            return self.status()

    def close(self):
        if self.thread and self.thread.is_alive():
            self.cancel()
        if self.thread:
            self.thread.join(timeout=25)


def router(setup):
    from fastapi import APIRouter
    from fastapi.responses import FileResponse

    api = APIRouter(prefix="/api/workstation/ai-setup")

    @api.get("")
    def status():
        from .creation import CreationManager

        return {**setup.status(), "generation": CreationManager.health()}

    @api.get("/preflight")
    def check():
        return preflight(setup.root)

    @api.post("/start")
    def start():
        return setup.start()

    @api.post("/cancel")
    def cancel():
        return setup.cancel()

    @api.get("/preview")
    def preview():
        path = setup.root / "verification/generated.wav"
        if not path.is_file():
            raise StudioError("Verification audio is not ready", 404)
        return FileResponse(path, media_type="audio/wav")

    return api
