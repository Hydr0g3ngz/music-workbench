"""Lightweight hardware advice plus conservative, explicit inference policies.

The UI never imports Torch. Workers validate the real CUDA runtime and current free
memory immediately before loading weights; an nvidia-smi result alone is not proof.
"""

import os
import subprocess
import time

_cached = None


def nvidia_gpus(refresh=False):
    global _cached
    if not refresh and _cached and time.monotonic() - _cached[0] < 30:
        return _cached[1]
    gpus, error = [], None
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.free,driver_version,compute_cap",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode:
            raise RuntimeError("NVIDIA driver probe failed")
        for line in result.stdout.strip().splitlines():
            index, name, total, free, driver, capability = [x.strip() for x in line.split(",")]
            gpus.append(
                {
                    "index": int(index),
                    "name": name,
                    "memory_mib": int(float(total)),
                    "free_mib": int(float(free)),
                    "driver": driver,
                    "capability": float(capability),
                }
            )
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        error = str(exc)
    _cached = (time.monotonic(), {"gpus": gpus, "probe_error": error})
    return _cached[1]


def cuda128_supported(gpu, *, ace=False):
    # Windows CUDA 12.8 wheels. Unknown architectures/drivers require manual setup.
    try:
        driver = int(gpu["driver"].split(".")[0])
        return driver >= 570 and gpu["capability"] >= (8.0 if ace else 7.5)
    except (KeyError, ValueError, TypeError):
        return False


def ace_profile(gpu, requested="auto"):
    if gpu["memory_mib"] < 8000 or gpu["capability"] < 8.0:
        raise ValueError("ACE-Step requires an NVIDIA Ampere or newer GPU with at least 8 GB VRAM")
    free = gpu["free_mib"]
    if free < 4000:
        raise ValueError("ACE-Step needs at least 4 GB free VRAM; close other GPU applications")
    if requested not in ("auto", "low-vram", "balanced", "quality"):
        raise ValueError("Unknown ACE-Step GPU profile")
    if requested == "auto":
        requested = "quality" if free >= 18000 else "balanced" if free >= 10000 else "low-vram"
    minimum = {"low-vram": 4000, "balanced": 10000, "quality": 18000}[requested]
    if free < minimum:
        raise ValueError(f"{requested} profile needs {minimum / 1000:g} GB free VRAM; choose Auto")
    return {
        "id": requested,
        "quantization": None if requested == "quality" else "int8_weight_only",
        "offload_to_cpu": requested != "quality",
        "offload_dit_to_cpu": requested == "low-vram",
        "dtype": "bfloat16",
        "gpu": gpu,
        "note": "Policies for 10–60 s, batch 1. Setup tests actual inference on your GPU; "
        "RTX 4070 Laptop 8 GB is the locally measured reference.",
    }


def ace_advice():
    probe = nvidia_gpus()
    eligible = [
        g for g in probe["gpus"] if cuda128_supported(g, ace=True) and g["memory_mib"] >= 8000
    ]
    if not eligible:
        return {**probe, "recommended": None}
    try:
        profile = ace_profile(max(eligible, key=lambda g: g["free_mib"]))
        return {**probe, "recommended": profile}
    except ValueError as error:
        return {**probe, "recommended": None, "message": str(error)}
