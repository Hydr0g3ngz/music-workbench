"""Isolated, offline ACE-Step inference. Never imported by the UI Python runtime."""

import hashlib
import json
import os
import shutil
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path


def write(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def checkpoint_backend():
    """Avoid Windows copy-on-write mmap reserving a whole checkpoint in commit.

    Called before importing Transformers, Diffusers or ACE-Step. This change is
    confined to the isolated inference process; the UI and other models keep
    their usual safetensors behavior. Pinned safetensors 0.8 supports pread.
    """
    if sys.platform != "win32":
        return "mmap"
    import safetensors
    import safetensors.torch

    original = safetensors.safe_open

    def open_checkpoint(*args, **kwargs):
        kwargs["backend"] = "pread"
        return original(*args, **kwargs)

    safetensors.safe_open = open_checkpoint
    safetensors.torch.safe_open = open_checkpoint
    return "pread"


def resources():
    import psutil
    import torch

    memory = psutil.Process().memory_info()
    data = {
        "resident_ram_mib": round(memory.rss / 1024**2, 1),
        "peak_allocated_mib": round(torch.cuda.max_memory_allocated() / 1024**2, 1),
        "peak_reserved_mib": round(torch.cuda.max_memory_reserved() / 1024**2, 1),
        "available_ram_mib": round(psutil.virtual_memory().available / 1024**2, 1),
        "cuda_free_mib": round(torch.cuda.mem_get_info()[0] / 1024**2, 1),
    }
    if hasattr(memory, "private"):
        data["private_commit_mib"] = round(memory.private / 1024**2, 1)
        data["peak_private_commit_mib"] = round(memory.peak_pagefile / 1024**2, 1)
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong)
                for name in (
                    "physical",
                    "available_physical",
                    "commit",
                    "available_commit",
                    "virtual",
                    "available_virtual",
                    "extended",
                )
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            data["available_system_commit_mib"] = round(status.available_commit / 1024**2, 1)
    if hasattr(memory, "peak_wset"):
        data["peak_resident_ram_mib"] = round(memory.peak_wset / 1024**2, 1)
    return data


def execute(request):
    if request.get("owner_pid"):
        from .task_worker import watch_owner

        threading.Thread(target=watch_owner, args=(request["owner_pid"],), daemon=True).start()
    runtime = request["runtime"]
    source = Path(runtime["source"]).resolve()
    checkpoints = Path(runtime["checkpoints"]).resolve()
    output = Path(request["output"]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    status = output / "progress.json"
    started = time.monotonic()

    def progress(fraction=0, desc=None, **_):
        if isinstance(fraction, (tuple, list)):
            fraction = fraction[0] / max(1, fraction[1])
        write(status, {"fraction": float(fraction), "message": str(desc or "Generating")[:300]})

    if runtime.get("weights_manifest_sha256"):
        progress(0, "Verifying pinned checkpoints")
        manifest = checkpoints / "music-studio-manifest.json"
        if hashlib.sha256(manifest.read_bytes()).hexdigest() != runtime["weights_manifest_sha256"]:
            raise RuntimeError("Checkpoint manifest changed; rerun setup to verify the snapshot")
        for item in json.loads(manifest.read_text(encoding="utf-8"))["files"]:
            path = (checkpoints / item["file"]).resolve()
            if not path.is_relative_to(checkpoints):
                raise RuntimeError("Invalid checkpoint manifest path")
            with path.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != item["sha256"]:
                raise RuntimeError("Checkpoint checksum mismatch: " + item["file"])

    os.environ.update(
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        HF_HUB_DISABLE_TELEMETRY="1",
        ACESTEP_CHECKPOINTS_DIR=str(checkpoints),
        TOKENIZERS_PARALLELISM="false",
        GRADIO_ANALYTICS_ENABLED="False",
    )
    sys.path.insert(0, str(source))
    from .windows_dlls import prepare_torch

    prepare_torch()
    import torch

    torch.set_grad_enabled(False)
    torch.set_num_threads(8)
    storage_backend = checkpoint_backend()
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music

    if not torch.cuda.is_available():
        raise RuntimeError("This creation profile requires an NVIDIA CUDA GPU")
    from .hardware import ace_profile

    devices = []
    for index in range(torch.cuda.device_count()):
        with torch.cuda.device(index):
            free, total = torch.cuda.mem_get_info()
        capability = torch.cuda.get_device_capability(index)
        devices.append(
            {
                "index": index,
                "name": torch.cuda.get_device_name(index),
                "memory_mib": total // 1024**2,
                "free_mib": free // 1024**2,
                "capability": capability[0] + capability[1] / 10,
            }
        )
    eligible = [g for g in devices if g["memory_mib"] >= 8000 and g["capability"] >= 8]
    if not eligible:
        raise RuntimeError("This ACE-Step build needs an Ampere or newer NVIDIA GPU with 8 GB VRAM")
    gpu = max(eligible, key=lambda g: g["free_mib"])
    torch.cuda.set_device(gpu["index"])
    profile = ace_profile(gpu, request["parameters"].get("gpu_profile", "auto"))
    # Exercise a kernel, not just driver detection, before loading large models.
    torch.ones(1, device="cuda").sum().item()
    torch.cuda.reset_peak_memory_stats()

    def record(stage):
        with (output / "resources.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"stage": stage, **resources()}) + "\n")

    record("before-models")

    class OfflineHandler(AceStepHandler):
        @contextmanager
        def _load_model_context(self, model_name):
            record("before-" + model_name)
            with super()._load_model_context(model_name):
                record("loaded-" + model_name)
                yield
            record("offloaded-" + model_name)

        def _ensure_models_present(self, **_):
            # Upstream's main-bundle check also downloads an unused 5Hz language model.
            # This profile deliberately uses only DiT + VAE + text encoder, without LM.
            required = (
                "acestep-v15-turbo/model.safetensors",
                "vae/diffusion_pytorch_model.safetensors",
                "Qwen3-Embedding-0.6B/model.safetensors",
            )
            missing = [name for name in required if not (checkpoints / name).is_file()]
            return ("Missing local components: " + ", ".join(missing), False) if missing else None

        @staticmethod
        def _sync_model_code_if_needed(config_path, checkpoint_path):
            # Keep the pinned model snapshot immutable. It already contains model code.
            return None

    progress(0, "Loading ACE-Step · " + profile["id"])
    handler = OfflineHandler()
    message, ready = handler.initialize_service(
        project_root=str(source),
        config_path="acestep-v15-turbo",
        device="cuda",
        use_flash_attention=False,
        compile_model=False,
        offload_to_cpu=profile["offload_to_cpu"],
        offload_dit_to_cpu=profile["offload_dit_to_cpu"],
        quantization=profile["quantization"],
        use_mlx_dit=False,
    )
    if not ready:
        raise RuntimeError(message)
    loaded = time.monotonic()
    record("initialized")
    if handler.quantization != profile["quantization"]:
        raise RuntimeError("Required quantization was disabled; repair the ACE-Step environment")
    options = request["parameters"]
    params = GenerationParams(
        task_type=options.get("mode", "text2music"),
        src_audio=request.get("reference_audio"),
        audio_cover_strength=options.get("reference_strength", 0.65),
        repainting_start=options.get("repaint_start", 0),
        repainting_end=options.get("repaint_end", -1),
        chunk_mask_mode="explicit" if options.get("mode") == "repaint" else "auto",
        enable_normalization=options.get("mode") != "repaint",
        caption=options["prompt"],
        lyrics="[Instrumental]" if options["instrumental"] else options["lyrics"],
        instrumental=options["instrumental"],
        vocal_language=options.get("language", "unknown"),
        bpm=round(options["bpm"]),
        keyscale=options.get("key", ""),
        timesignature="4",
        duration=options["duration"],
        seed=options["seed"],
        inference_steps=options["steps"],
        thinking=False,
        use_cot_caption=False,
        use_cot_language=False,
        use_cot_metas=False,
        use_cot_lyrics=False,
    )
    config = GenerationConfig(
        batch_size=1,
        allow_lm_batch=False,
        use_random_seed=False,
        seeds=[options["seed"]],
        audio_format="wav",
    )
    progress(0.05, "Generating a draft")
    result = generate_music(handler, None, params, config, save_dir=str(output), progress=progress)
    if not result.success or not result.audios or not result.audios[0].get("path"):
        raise RuntimeError(result.error or result.status_message or "ACE-Step produced no audio")
    generated = Path(result.audios[0]["path"]).resolve()
    if not generated.is_relative_to(output) or not generated.is_file():
        raise RuntimeError("ACE-Step returned an invalid output path")
    target = output / "generated.wav"
    if generated != target:
        shutil.copyfile(generated, target)
    torch.cuda.synchronize()
    metrics = {
        "load_seconds": round(loaded - started, 3),
        "generation_seconds": round(time.monotonic() - loaded, 3),
        "total_seconds": round(time.monotonic() - started, 3),
        "device": torch.cuda.get_device_name(),
        "torch": torch.__version__,
        "language_model": False,
        "profile": profile,
        "offload": profile["offload_to_cpu"],
        "quantization": profile["quantization"],
        "quantization_scope": "DiT decoder linear weights only; "
        "VAE/text encoder remain floating point",
        "grad_enabled": torch.is_grad_enabled(),
        "cpu_threads": torch.get_num_threads(),
        "checkpoint_backend": storage_backend,
        **resources(),
    }
    write(output / "result.json", {"file": target.name, "metrics": metrics})
    progress(1, "Draft ready")
    print(json.dumps(metrics), flush=True)


if __name__ == "__main__":
    request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    started = time.monotonic()
    try:
        execute(request)
    except Exception as error:
        try:
            output = Path(request["output"])
            output.mkdir(parents=True, exist_ok=True)
            write(
                output / "failure.json",
                {
                    "error": str(error),
                    "metrics": {
                        "total_seconds": round(time.monotonic() - started, 3),
                        **resources(),
                    },
                },
            )
        except Exception:
            pass
        raise
