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
    "piano-notes": {
        "title": ["钢琴多音音符 · Transkun", "Piano notes · Transkun"],
        "description": [
            "钢琴专用转录；估计音高、起止与力度，试听后进入钢琴卷帘修改。",
            "Piano-specific pitch, timing and velocity estimates; "
            "audition and edit in the piano roll.",
        ],
        "models": ["transkun-piano"],
        "device": "cuda",
        "min_vram_mib": 4000,
        "required_free_bytes": 10 * 1024**3,
        "download_estimate": "3–5 GB",
        "backend": "Transkun 2.0.1 · FP32 · Torch CUDA 12.8 · 16 s windows",
        "license": "MIT (upstream source and bundled checkpoint)",
        "source": "https://github.com/Yujia-Yan/Transkun",
        "entry": "/station.html?tools=piano-notes",
    },
    "polyphonic-notes": {
        "title": ["多音音符 · Basic Pitch", "Polyphonic notes · Basic Pitch"],
        "description": [
            "Basic Pitch 多音转录，适合独奏乐器。试听音符后加入钢琴卷帘；整曲混音先分轨。",
            "Basic Pitch polyphony for a solo instrument. Audition and edit notes; "
            "separate mixtures first.",
        ],
        "models": ["basic-pitch"],
        "device": "cpu",
        "required_free_bytes": 2 * 1024**3,
        "download_estimate": "150–350 MB",
        "backend": "Spotify Basic Pitch 0.4.0 · ONNX CPU · 230 KB checkpoint",
        "license": "Apache-2.0 (Spotify code and bundled model)",
        "source": "https://github.com/spotify/basic-pitch",
        "entry": "/station.html?tools=polyphonic-notes",
    },
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
PACKS["music-tools-cuda"] = {
    **PACKS["music-tools"],
    "title": ["分轨、旋律与转写 · NVIDIA 加速", "Stems, melody & transcription · NVIDIA"],
    "description": [
        "为支持的 NVIDIA 显卡准备独立 CUDA 环境。保留 CPU 工具包，可自行选择设备。",
        "Private CUDA runtime for supported NVIDIA GPUs. Keep the CPU pack and choose the device.",
    ],
    "device": "cuda",
    "required_free_bytes": 10 * 1024**3,
    "download_estimate": "3–5 GB",
    "entry": "/station.html?tools=music-tools-cuda",
}
PACKS["vocal-separation"] = {
    "title": ["人声与伴奏 · RoFormer", "Vocals & backing · RoFormer"],
    "description": [
        "分离人声与伴奏，试听后替换片段或加入新轨。准备独立 NVIDIA 环境。",
        "Separate vocals and backing; audition, then replace a clip or add tracks. "
        "Private NVIDIA runtime.",
    ],
    "models": ["mel-band-roformer-kj"],
    "device": "cuda",
    "required_free_bytes": 12 * 1024**3,
    "download_estimate": "4–6 GB",
    "backend": "Mel-Band RoFormer KJ · Torch CUDA 12.8",
    "license": "MIT (code and model card)",
    "source": "https://huggingface.co/KimberleyJSN/melbandroformer",
    "entry": "/station.html?tools=vocal-separation",
}
PACKS["qwen-transcription"] = {
    "title": ["语音、歌词与逐字定位 · Qwen", "Speech, lyrics & word timing · Qwen"],
    "description": [
        "Qwen 转写后用独立模型定位字词。可改错字、导出字幕；歌唱时间仍需试听核对。",
        "Transcribe with Qwen, then locate words acoustically. Edit text and export subtitles; "
        "check singing by ear.",
    ],
    "models": ["qwen3-asr"],
    "device": "cuda",
    "min_capability": 8.0,
    "min_vram_mib": 8000,
    "required_free_bytes": 24 * 1024**3,
    "download_estimate": "10–13 GB",
    "backend": "Qwen3-ASR-1.7B + Qwen3-ForcedAligner-0.6B · BF16 · sequential loading",
    "license": "Apache-2.0",
    "source": "https://github.com/QwenLM/Qwen3-ASR",
    "entry": "/station.html?tools=qwen-transcription",
}


def packs_root():
    return data_root() / "AI" / "tools"


def pack_for(model):
    return next((key for key, spec in PACKS.items() if model in spec["models"]), None)


def managed_runtime(model, device="auto"):
    """Cheap discovery only. A verified manifest is published after offline inference."""
    key = pack_for(model)
    if not key:
        return None
    if key == "music-tools":
        cpu = published_runtime(packs_root() / key, key)
        accelerated = published_runtime(packs_root() / "music-tools-cuda", "music-tools-cuda")
        if device == "cpu":
            return cpu or accelerated
        return accelerated or (cpu if device == "auto" else None)
    if device == "cuda" and PACKS[key].get("device") != "cuda":
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
    gpus = []
    if spec.get("device") == "cuda":
        from .hardware import cuda128_supported, nvidia_gpus

        gpus = nvidia_gpus()["gpus"]
        if not any(
            cuda128_supported(g)
            and g["capability"] >= spec.get("min_capability", 7.5)
            and g["memory_mib"] >= spec.get("min_vram_mib", 4000)
            for g in gpus
        ):
            reasons.append("cuda-compatibility")
    return {
        "supported": not reasons,
        "reasons": reasons,
        "free_bytes": free,
        "required_free_bytes": spec["required_free_bytes"],
        "directory": str(root),
        "device": spec.get("device", "cpu"),
        "gpus": gpus,
        "min_capability": spec.get("min_capability", 7.5),
        "min_vram_mib": spec.get("min_vram_mib", 4000),
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
        checks = [
            self.registry.describe(model, device=PACKS[key].get("device", "cpu"))
            for model in PACKS[key]["models"]
        ]
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
            self.registry.check(model, device=PACKS[key].get("device", "cpu"))
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
