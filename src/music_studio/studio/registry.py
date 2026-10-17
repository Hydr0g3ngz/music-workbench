"""Fixed local capabilities. Package presence, native imports and weights are separate.

Only launch-time configured Python interpreters are used. HTTP/agent arguments
cannot select executables, model repositories, code, or download URLs.
"""

import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path

from ..config import Settings
from ..io import read_json, write_json
from ..lyric_models import MODELS
from .process import TaskStopped, log_tail, run_owned
from .service import StudioError

CATALOG = {
    "musical-analysis": {
        "title": ["素材速度、调性与电平分析", "Material tempo, key & levels"],
        "description": [
            "Librosa 全局估计；报告节拍与调性分差。可能存在半速/倍速与转调误判。DSP，无神经权重。",
            "Global librosa estimates with beats and key margin. Tempo/key may be ambiguous. "
            "DSP, no neural weights.",
        ],
        "runtime": "inference",
        "imports": ["librosa", "scipy", "soundfile"],
        "stage": "musical",
        "device": "cpu",
        "license": "ISC (librosa)",
        "source": "https://github.com/librosa/librosa",
    },
    "time-pitch": {
        "title": ["素材独立变速与变调", "Independent time & pitch"],
        "description": [
            "Librosa 相位声码器；生成候选后试听替换，可撤销。DSP，复杂音乐可能出现瞬态失真。",
            "Librosa phase vocoder. Audition before reversible replacement. "
            "DSP; transients may smear.",
        ],
        "runtime": "inference",
        "imports": ["librosa", "scipy", "soundfile"],
        "stage": "transform",
        "device": "cpu",
        "license": "ISC (librosa)",
        "source": "https://github.com/librosa/librosa",
    },
    "demucs-four-stems": {
        "title": ["四分轨 · 鼓 / 贝斯 / 人声 / 其他", "Four stems · drums / bass / vocals / other"],
        "description": [
            "Demucs htdemucs；对齐四条音轨，可独立编排、混音与替换。",
            "Demucs htdemucs. Four aligned stems for rearrangement and mixing.",
        ],
        "runtime": "inference",
        "imports": ["torch", "torchaudio", "demucs.pretrained", "demucs.apply"],
        "stage": "separate",
        "license": "MIT",
        "weight_id": "955717e8-8726e21a",
        "source": "https://github.com/facebookresearch/demucs",
    },
    "mel-band-roformer-kj": {
        "title": [
            "分离人声与伴奏 · Mel-Band RoFormer",
            "Separate vocals & backing · Mel-Band RoFormer",
        ],
        "description": [
            "可选本地模型，8 秒窗口、单批次。先试听结果，再加入编排。",
            "Optional local model, 8 s windows, batch 1. Audition before adding stems.",
        ],
        "runtime": "separation",
        "imports": ["torch", "librosa", "ml_collections", "rotary_embedding_torch", "beartype"],
        "stage": "separate",
        "license": "MIT (code and model card)",
        "weight_id": "KimberleyJSN/melbandroformer@ac9b0614ab3cd7f77219e18ba494dfd93956c348",
        "source": "https://huggingface.co/KimberleyJSN/melbandroformer",
    },
    "inspect": {
        "title": ["检查音频电平", "Inspect audio levels"],
        "description": [
            "测量峰值、RMS 和满刻度采样，不需要模型。",
            "Measure peak, RMS and full-scale samples. No model needed.",
        ],
        "runtime": "base",
        "imports": ["numpy", "soundfile"],
        "stage": "inspect",
        "device": "cpu",
        "license": "MIT (Music Studio)",
        "source": "https://github.com/Hydr0g3ngz/music-studio",
    },
    "loudness-ebur128": {
        "title": ["测量听感响度与真峰值", "Measure loudness & true peak"],
        "description": [
            "LUFS、真峰值与响度范围；无需模型。短于 0.4 秒不报告整段响度。",
            "LUFS, true peak and loudness range. No model. Integrated loudness needs 0.4 s.",
        ],
        "runtime": "base",
        "imports": ["pyebur128", "numpy", "soundfile"],
        "stage": "loudness",
        "device": "cpu",
        "license": "MIT (libebur128 / pyebur128)",
        "source": "https://github.com/jodhus/pyebur128",
    },
    "gtcrn": {
        "title": [
            "轻量语音降噪 · GTCRN（实验）",
            "Lightweight speech cleanup · GTCRN (experimental)",
        ],
        "description": [
            "轻量 CPU 语音降噪，强度可调。内部 16 kHz，可能损伤音乐、环境声与高频；原音保留。",
            "Lightweight CPU speech cleanup. Internal 16 kHz; may alter music, "
            "ambience and high frequencies. Originals retained.",
        ],
        "runtime": "base",
        "imports": ["sherpa_onnx", "pyebur128", "av", "numpy", "soundfile"],
        "stage": "denoise",
        "device": "cpu",
        "license": "MIT (GTCRN); Apache-2.0 (sherpa-onnx)",
        "installable_weights": True,
        "download_bytes": 535638,
        "weight_file": "gtcrn_simple.onnx",
        "weight_id": "gtcrn_simple.onnx@"
        "e77603ac0c23dac3227dd2d7135b3a585cbee2679048aecfa886657d3ae1b534",
        "source": "https://github.com/Xiaobin-Rong/gtcrn",
    },
    "dpdfnet2-48k": {
        "title": ["语音清理 · DPDFNet 48 kHz", "Speech cleanup · DPDFNet 48 kHz"],
        "description": [
            "48 kHz CPU 语音增强。处理音乐或环境声可能失真；"
            "强度可调，原音保留，提供匹配响度的 A/B 试听。",
            "48 kHz CPU speech enhancement. May alter music or ambience. "
            "Adjustable strength, retained originals and loudness-matched A/B playback.",
        ],
        "runtime": "base",
        "imports": ["sherpa_onnx", "pyebur128", "av", "numpy", "soundfile"],
        "stage": "denoise",
        "device": "cpu",
        "license": "Apache-2.0",
        "installable_weights": True,
        "download_bytes": 10596848,
        "weight_file": "dpdfnet2_48khz_hr.onnx",
        "weight_id": "dpdfnet2_48khz_hr.onnx@"
        "0b399f8a58dc4d70d8cd97541f5c39869406145193b957d00a03b66070944928",
        "source": "https://huggingface.co/Ceva-IP/DPDFNet",
    },
    "demucs-htdemucs": {
        "title": ["分离人声与伴奏", "Separate vocals & backing"],
        "description": [
            "Demucs 分离两个对齐音轨；伴奏保留原音残差。",
            "Demucs produces two aligned stems with mixture-consistent backing.",
        ],
        "runtime": "inference",
        "imports": ["torch", "torchaudio", "demucs.pretrained", "demucs.apply"],
        "stage": "separate",
        "license": "MIT",
        "weight_id": "955717e8-8726e21a",
        "source": "https://github.com/facebookresearch/demucs",
    },
    "whisper-small": {
        "title": ["识别语音与歌词", "Transcribe speech & lyrics"],
        "description": [
            "Whisper small；可编辑转写，歌唱与复杂混音可能出错。",
            "Whisper small. Editable transcript; singing and mixtures can cause errors.",
        ],
        "runtime": "inference",
        "imports": ["torch", "faster_whisper", "ctranslate2", "librosa"],
        "stage": "lyrics",
        "license": "MIT",
        "weight_id": "Systran/faster-whisper-small@536b0662742c02347bc0e980a01041f333bce120",
        "source": "https://huggingface.co/Systran/faster-whisper-small",
    },
    "qwen3-asr": {
        "title": ["Qwen 语音与歌词", "Qwen speech & lyrics"],
        "description": [
            "独立 Qwen3-ASR-1.7B 环境；按需加载，不常驻显存。",
            "Isolated Qwen3-ASR-1.7B runtime. Loaded only while its task runs.",
        ],
        "runtime": "lyrics",
        "imports": ["torch", "qwen_asr", "transformers", "librosa"],
        "stage": "lyrics",
        "license": "Apache-2.0",
        "weight_id": "@".join(MODELS["qwen"]),
        "source": "https://huggingface.co/Qwen/Qwen3-ASR-1.7B",
    },
    "crepe-rest": {
        "title": ["提取旋律 · 保留休止（实验）", "Extract melody · preserve rests (experimental)"],
        "description": [
            "CREPE 单旋律估计；保留间隙，提供 MIDI 与合成对照。部分音源会退步，可与旧版比较。",
            "CREPE with gaps, MIDI and synthesis. Compare with legacy; some sources regress.",
        ],
        "runtime": "inference",
        "imports": ["torch", "torchcrepe", "librosa", "scipy"],
        "stage": "melody",
        "license": "MIT",
        "weight_id": "torchcrepe/0.0.24/full.pth",
        "source": "https://github.com/maxrmorrison/torchcrepe",
    },
    "crepe-stable": {
        "title": ["提取旋律 · 旧版对照", "Extract melody · legacy comparison"],
        "description": [
            "保留旧解码器，用于同一音频的公平比较。",
            "Retains the legacy decoder for comparisons on the same audio.",
        ],
        "runtime": "inference",
        "imports": ["torch", "torchcrepe", "librosa", "scipy"],
        "stage": "melody",
        "license": "MIT",
        "weight_id": "torchcrepe/0.0.24/full.pth",
        "source": "https://github.com/maxrmorrison/torchcrepe",
    },
    "beats-librosa": {
        "title": ["检测节拍与速度", "Find beats & tempo"],
        "description": [
            "Librosa 打击乐分量节拍估计；不下载神经网络。",
            "Librosa percussive beat estimation. No neural weights required.",
        ],
        "runtime": "inference",
        "imports": ["librosa", "scipy"],
        "stage": "rhythm",
        "device": "cpu",
        "license": "ISC (librosa)",
        "source": "https://github.com/librosa/librosa",
    },
}


def child_environment(model_dir: str) -> dict:
    environment = os.environ.copy()
    environment.update(
        PYTHONUTF8="1",
        PYTHONUNBUFFERED="1",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=str(Path(__file__).resolve().parents[2]),
        HF_HUB_OFFLINE="1",
        HF_HUB_DISABLE_TELEMETRY="1",
        TRANSFORMERS_OFFLINE="1",
        TORCH_HOME=str(Path(model_dir) / "torch"),
    )
    return environment


class ModelRegistry:
    def __init__(self, service, settings: Settings | None = None):
        self.service = service
        self.config_file = service.root / ".studio-runtime.json"
        if self.config_file.is_symlink():
            raise StudioError("Invalid runtime configuration")
        if settings is None and self.config_file.is_file():
            settings = Settings.model_validate(read_json(self.config_file))
        self.settings = (settings or Settings()).resolved()
        if settings is not None:
            write_json(self.config_file, self.settings.model_dump())
        self.health = {}
        self.lock = threading.Lock()

    def python(self, spec, device="auto"):
        slot = spec["runtime"]
        if slot == "separation":
            from .separation import runtime

            return runtime()["python"]
        configured = (
            self.settings.lyrics_python
            if slot == "lyrics"
            else self.settings.inference_python
            if slot == "inference"
            else None
        )
        if configured:
            return str(Path(configured).expanduser().resolve())
        managed = self.managed(spec, device)
        if managed:
            from .model_setup import bind_app

            bind_app(managed["python"])
            return managed["python"]
        return sys.executable

    def managed(self, spec, device="auto"):
        # Explicit launch settings remain authoritative; installer users need no settings.
        if spec["runtime"] == "inference" and self.settings.inference_python:
            return None
        from .model_setup import managed_runtime

        if device == "auto":
            device = self.settings.device
        key = next((k for k, value in CATALOG.items() if value is spec), None)
        if spec.get("device") == "cpu":
            device = "cpu"
        return managed_runtime(key, device) if key else None

    def environment_settings(self, model, device="auto"):
        managed = self.managed(self.spec(model), device)
        return {"model_dir": managed["model_dir"]} if managed else {}

    def spec(self, model):
        if model not in CATALOG:
            raise StudioError("Unknown local model", 404)
        return CATALOG[model]

    def _probe(self, model, deep=False, cancelled=lambda: False, device="auto"):
        spec = self.spec(model)
        try:
            python = self.python(spec, device)
            managed = self.managed(spec, device)
            if deep and managed:
                from .model_setup import pack_for, packs_root, verify_files

                verify_files(managed, packs_root() / managed.get("pack", pack_for(model)))
            if spec["runtime"] == "separation":
                from .separation import runtime

                runtime(verify=deep)
        except (OSError, ValueError, KeyError) as error:
            return {
                "state": "missing",
                "error": str(error),
                "weights": False,
            }
        if not Path(python).is_file():
            return {
                "state": "missing",
                "error": "Configured Python does not exist",
                "weights": False,
            }
        # Child handles native-loader crashes and reports through one JSON line.
        script = """
import hashlib, importlib, importlib.metadata, importlib.util, json, pathlib, sys
spec, root, deep = json.loads(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3] == '1'
modules = sorted({n.split('.')[0] for n in spec['imports']})
missing = [n for n in modules if importlib.util.find_spec(n) is None]
weights = []
stage = spec['stage']
if stage == 'separate' and spec['runtime'] != 'separation':
    weights = [root/'torch/hub/checkpoints/955717e8-8726e21a.th']
elif stage == 'denoise': weights = [root/'cleanup'/spec['weight_file']]
elif spec.get('weight_id', '').startswith('Systran/'):
    folder = root/'whisper/models--Systran--faster-whisper-small/snapshots'
    folder = folder/'536b0662742c02347bc0e980a01041f333bce120'
    weights = [folder/n for n in ('config.json','model.bin','tokenizer.json','vocabulary.txt')]
elif spec['runtime'] == 'lyrics':
    revision = spec['weight_id'].split('@')[1]
    folder = root/'lyrics/qwen'/revision
    if not (folder/'config.json').is_file():
        folder = root/'huggingface/models--Qwen--Qwen3-ASR-1.7B/snapshots'/revision
    names = ('config.json', 'model.safetensors.index.json',
      'model-00001-of-00002.safetensors', 'model-00002-of-00002.safetensors',
      'tokenizer_config.json', 'vocab.json', 'merges.txt', 'preprocessor_config.json')
    weights = [folder/n for n in names]
elif stage == 'melody':
    package = importlib.util.find_spec('torchcrepe')
    weights = [pathlib.Path(package.origin).parent/'assets/full.pth'] if package else []
    if not package: weights = [root/'missing-crepe']
if deep and not missing:
    for name in spec['imports']: importlib.import_module(name)
versions = {}
for module in modules:
    aliases = {'faster_whisper':'faster-whisper','qwen_asr':'qwen-asr',
               'sherpa_onnx':'sherpa-onnx'}
    package = aliases.get(module,module)
    try: versions[package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError: pass
result = {'state':'missing' if missing else 'verified' if deep else 'unchecked', 'missing':missing,
 'weights':all(p.is_file() and p.stat().st_size > 0 for p in weights),
 'weight_bytes':sum(p.stat().st_size for p in weights if p.is_file()),
 'weight_files':len(weights),'versions':versions,'python':sys.version.split()[0],
 'cuda':None,'checked_at':__import__('time').time()}
if stage == 'denoise' and result['weights']:
    result['weight_sha256'] = hashlib.sha256(weights[0].read_bytes()).hexdigest()
    result['weights'] = result['weight_sha256'] == spec['weight_id'].split('@')[1]
if deep and not missing and 'torch' in modules:
    import torch
    result['cuda'] = torch.cuda.is_available()
print('MUSIC_STUDIO_HEALTH:'+json.dumps(result))
"""
        try:
            folder = self.service.root / ".studio-health"
            if folder.is_symlink():
                raise StudioError("Invalid runtime health directory")
            folder.mkdir(exist_ok=True)
            log = folder / f"{uuid.uuid4().hex}.log"
            code = run_owned(
                [
                    python,
                    "-X",
                    "utf8",
                    "-c",
                    script,
                    json.dumps(spec),
                    self.environment_settings(model, device).get(
                        "model_dir", self.settings.model_dir
                    ),
                    "1" if deep else "0",
                ],
                log,
                child_environment(
                    self.environment_settings(model, device).get(
                        "model_dir", self.settings.model_dir
                    )
                ),
                timeout=90,
                cancelled=cancelled,
            )
            output = log_tail(log, 65536)
            lines = [
                line for line in output.splitlines() if line.startswith("MUSIC_STUDIO_HEALTH:")
            ]
            if code or not lines:
                return {
                    "state": "failed",
                    "error": f"Runtime import exited {code}: " + output[-1800:],
                    "weights": False,
                }
            result = json.loads(lines[-1].split(":", 1)[1])
            if device == "cuda" and not spec.get("device") and deep and not result.get("cuda"):
                result.update(
                    state="failed",
                    error="CUDA is unavailable in this runtime; "
                    "install the NVIDIA tool pack or choose CPU",
                )
            if spec["runtime"] == "separation":
                checkpoint = Path(runtime()["root"]) / "MelBandRoformer.ckpt"
                result.update(weight_files=1, weight_bytes=checkpoint.stat().st_size)
            return result
        except TaskStopped:
            raise
        except (OSError, TimeoutError, ValueError) as error:
            return {"state": "failed", "error": str(error), "weights": False}

    def cache_key(self, model, device):
        device = self.spec(model).get("device", device)
        return model if device == "auto" else model + ":" + device

    def runtime_identity(self, model, device):
        try:
            return self.python(self.spec(model), device)
        except (OSError, ValueError, KeyError):
            return None

    def check(self, model, *, deep=True, cancelled=lambda: False, device="auto"):
        # Serialize optional native imports so several clients cannot flood GPU initialization.
        with self.lock:
            found = self._probe(model, deep, cancelled, device)
            found.setdefault("checked_at", time.time())
            found["runtime_python"] = self.runtime_identity(model, device)
            self.health[self.cache_key(model, device)] = found
        return self.describe(model, found, device)

    def describe(self, model, health=None, device="auto"):
        from .model_setup import pack_for

        spec = self.spec(model)
        found = health or self.health.get(self.cache_key(model, device))
        managed = self.managed(spec, device)
        if managed and (
            not found
            or found.get("checked_at", 0) < managed["installed_at"]
            or found.get("runtime_python", managed["python"]) != managed["python"]
        ):
            # Setup already ran every capability offline. Enable the UI immediately;
            # require() still performs a fresh deep check before the first task.
            found = {
                "state": "verified",
                "weights": True,
                "checked_at": 0,
                "cuda": managed.get("device") == "cuda",
                "source": "offline-install-verification",
            }
        if found is None:
            # No model runtime is imported merely by opening the page.
            found = {"state": "unchecked", "weights": None}
        setup_pack = pack_for(model)
        if setup_pack == "music-tools" and device == "cuda":
            setup_pack = "music-tools-cuda"
        return {
            "id": model,
            **{k: v for k, v in spec.items() if k != "imports"},
            "health": found,
            "offline": True,
            "execution_device": spec.get("device")
            or (
                "cpu"
                if device == "cpu" or (device == "auto" and self.settings.device == "cpu")
                else "cuda"
                if found.get("cuda")
                else "cpu"
                if found.get("cuda") is False
                else "unchecked"
            ),
            "runtime_source": "managed" if managed else "configured",
            "devices": (
                ["cpu"]
                if spec.get("device") == "cpu"
                else ["cpu", "cuda"]
                if found.get("cuda")
                else ["cpu"]
            ),
            "setup_pack": setup_pack,
            "setup_url": ("/ai-setup.html#" + setup_pack if setup_pack else None),
            "max_duration_seconds": 7200 if spec["stage"] in ("inspect", "loudness") else 600,
            "runnable": found["state"] == "verified" and found.get("weights") is True,
            "resource_note": "One local task at a time; memory depends on audio, "
            "device and runtime.",
        }

    def list(self):
        return [self.describe(key) for key in CATALOG]

    def install_weights(self, model):
        # This separate UI action is the only network-enabled setup endpoint.
        # It cannot install packages, execute code or choose a URL/directory.
        if model not in ("gtcrn", "dpdfnet2-48k"):
            raise StudioError("This model has no built-in weight installer", 404)
        checked = self.check(model)
        if checked["health"]["state"] != "verified":
            raise StudioError(
                "Restart Next to update its CPU runtime, then check the model again", 503
            )
        from .cleanup import download

        with self.lock:
            download(
                self.environment_settings(model).get("model_dir", self.settings.model_dir), model
            )
            self.health.pop(model, None)
        return self.check(model)

    def require(self, model, cancelled=lambda: False, device="auto"):
        found = self.health.get(self.cache_key(model, device))
        managed = self.managed(self.spec(model), device)
        if (
            not found
            or found["state"] != "verified"
            or time.time() - found.get("checked_at", 0) > 300
            or found.get("runtime_python") != self.runtime_identity(model, device)
            or (managed and found.get("checked_at", 0) < managed["installed_at"])
        ):
            self.check(model, cancelled=cancelled, device=device)
        result = self.describe(model, device=device)
        if not result["runnable"]:
            health = result["health"]
            reason = health.get("error") or (
                "Missing packages: " + ", ".join(health.get("missing", []))
                if health["state"] == "missing"
                else "Pinned model weights are not cached"
            )
            if result.get("setup_url"):
                reason += ". Open AI setup to prepare this tool: " + result["setup_url"]
            raise StudioError(reason + ". No download was started.", 503)
        return self.spec(model)
