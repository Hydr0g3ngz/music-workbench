"""Managed optional tool packs; inference never installs or downloads anything."""

import os
import platform
import shutil
import sys
from pathlib import Path

from ..io import read_json, sha256
from .ai_setup import ACTIVE, AISetup, data_root
from .service import StudioError

PACKS = {
    "music-tools": {
        "title": ["分轨、旋律与转写", "Stems, melody & transcription"],
        "description": [
            "拆成四条声部，把哼唱变成 MIDI，识别语音与歌词。",
            "Separate four stems, turn humming into MIDI, transcribe speech and lyrics.",
        ],
        "models": [
            "demucs-four-stems",
            "demucs-htdemucs",
            "crepe-rest",
            "crepe-stable",
            "whisper-small",
            "musical-analysis",
            "time-pitch",
            "beats-librosa",
        ],
        "required_free_bytes": 6 * 1024**3,
        "download_estimate": "1–2 GB",
        "backend": "Demucs htdemucs · CREPE · Whisper small · librosa",
        "license": "MIT; ISC (librosa)",
        "source": "https://github.com/facebookresearch/demucs",
        "entry": "/station.html?tools=music-tools",
    },
    "speech-cleanup": {
        "title": ["清理讲话录音", "Clean speech recordings"],
        "description": [
            "降低讲话录音的背景噪声，保留原音并提供前后试听。适合口播，不适合整首音乐。",
            "Reduce background noise in speech, keeping originals for A/B listening. For speech.",
        ],
        "models": ["dpdfnet2-48k", "gtcrn"],
        "required_free_bytes": 1024**3,
        "download_estimate": "150–300 MB",
        "backend": "DPDFNet2 48 kHz · GTCRN · sherpa-onnx",
        "license": "Apache-2.0; MIT (GTCRN)",
        "source": "https://github.com/k2-fsa/sherpa-onnx",
        "entry": "/station.html?tools=speech-cleanup",
    },
}


def packs_root():
    return data_root() / "AI" / "tools"


def pack_for(model):
    return next((key for key, spec in PACKS.items() if model in spec["models"]), None)


def managed_runtime(model):
    """Cheap discovery only. A verified manifest is published after offline inference."""
    key = pack_for(model)
    if not key:
        return None
    return published_runtime(packs_root() / key, key)


def published_runtime(root, key):
    """The setup page and task registry must agree when files are removed."""
    try:
        value = read_json(root / "runtime.json")
        if (
            value.get("pack") != key
            or value.get("schema") != 1
            or set(value.get("verification", {})) != set(PACKS[key]["models"])
            or not Path(value["python"]).is_file()
            or not Path(value["model_dir"]).is_dir()
            or not value.get("files")
        ):
            return None
        for item in value["files"]:
            path = (root / item["file"]).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                return None
        value["installed_at"] = (root / "runtime.json").stat().st_mtime
        return value
    except (OSError, ValueError, KeyError, TypeError):
        return None


def verify_files(config, root):
    """Reject missing/corrupt checkpoints before declaring a managed tool runnable."""
    root = Path(root).resolve()
    files = config.get("files", [])
    if not files:
        raise ValueError("Tool checkpoint manifest is empty; repair its setup")
    for item in files:
        path = (root / item["file"]).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256(path) != item["sha256"]:
            raise ValueError("Tool checkpoint changed; repair setup: " + item["file"])


def bind_app(python):
    """Embedded Python ignores PYTHONPATH. Bind the current app after private dependencies.

    This also follows app upgrades and moves, without preserving a stale app copy in AI storage.
    """
    pth = Path(python).parent / "python312._pth"
    content = (
        "python312.zip\n.\nLib/site-packages\n" + str(Path(__file__).parents[2]) + "\nimport site\n"
    )
    if pth.is_file() and pth.read_text(encoding="utf-8") != content:
        pth.write_text(content, encoding="utf-8")


def preflight(root, pack):
    spec = PACKS[pack]
    root.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(root).free
    reasons = []
    if os.name != "nt" or platform.machine().lower() not in ("amd64", "x86_64"):
        reasons.append("windows-x64")
    if free < spec["required_free_bytes"]:
        reasons.append("disk-space")
    return {
        "supported": not reasons,
        "reasons": reasons,
        "free_bytes": free,
        "required_free_bytes": spec["required_free_bytes"],
        "directory": str(root),
        "device": "cpu",
        "download_estimate": spec["download_estimate"],
    }


class ToolSetup(AISetup):
    def __init__(self, pack, root):
        self.pack = pack
        super().__init__(root)

    def preflight(self):
        return preflight(self.root, self.pack)

    def command(self):
        return [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "music_studio.studio.model_install_worker",
            "--root",
            str(self.root),
            "--pack",
            self.pack,
            "--owner-pid",
            str(os.getpid()),
        ]


class ModelSetup:
    def __init__(self, registry, root=None):
        self.registry = registry
        self.root = root or packs_root()
        self.jobs = {key: ToolSetup(key, self.root / key) for key in PACKS}

    def get(self, key):
        if key not in self.jobs:
            raise StudioError("Unknown tool pack", 404)
        return self.jobs[key]

    def describe(self, key):
        job = self.get(key)
        state = job.status()
        installed = published_runtime(job.root, key)
        checks = [self.registry.describe(model) for model in PACKS[key]["models"]]
        checked_failure = any(
            m["health"]["state"] not in ("unchecked",) and not m["runnable"] for m in checks
        )
        return {
            "id": key,
            **PACKS[key],
            **state,
            "preflight": job.preflight(),
            "installed": bool(
                installed
                and installed.get("verification")
                and not checked_failure
                and Path(installed.get("python", "")).is_file()
                and Path(installed.get("model_dir", "")).is_dir()
            ),
            "checked": all(m["runnable"] for m in checks),
            "capabilities": checks,
            "verification": installed.get("verification") if installed else None,
        }

    def check(self, key):
        if self.get(key).status()["state"] in ACTIVE:
            raise StudioError("Wait for setup to finish before checking", 409)
        for model in PACKS[key]["models"]:
            self.registry.check(model)
        return self.describe(key)

    def close(self):
        for job in self.jobs.values():
            job.close()


def router(setup):
    from fastapi import APIRouter

    api = APIRouter(prefix="/api/workstation/model-setup")

    @api.get("")
    def listing():
        return [setup.describe(key) for key in PACKS]

    @api.post("/{key}/start")
    def start(key: str):
        setup.get(key).start()
        # Invalidate even a cached missing-runtime result after an install/retry.
        setup.registry.health.clear()
        return setup.describe(key)

    @api.post("/{key}/cancel")
    def cancel(key: str):
        setup.get(key).cancel()
        return setup.describe(key)

    @api.post("/{key}/check")
    def check(key: str):
        return setup.check(key)

    return api
