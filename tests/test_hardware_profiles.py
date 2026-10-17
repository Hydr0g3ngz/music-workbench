import sys

import pytest

from music_studio.config import Settings
from music_studio.io import write_json
from music_studio.studio import hardware, model_setup
from music_studio.studio.registry import ModelRegistry


def gpu(total=8188, free=7500, capability=8.9, driver="591.74"):
    return {
        "index": 0,
        "name": "fixture GPU",
        "memory_mib": total,
        "free_mib": free,
        "capability": capability,
        "driver": driver,
    }


def test_ace_uses_free_memory_and_rejects_unsupported_explicit_profiles():
    profile = hardware.ace_profile(gpu())
    assert profile["id"] == "low-vram"
    assert profile["offload_dit_to_cpu"] and profile["quantization"] == "int8_weight_only"
    assert hardware.ace_profile(gpu(24576, 11000))["id"] == "balanced"
    assert hardware.ace_profile(gpu(24576, 21000))["quantization"] is None
    # A busy 24 GB GPU must use the same conservative path as an 8 GB GPU.
    assert hardware.ace_profile(gpu(24576, 5000))["id"] == "low-vram"
    with pytest.raises(ValueError, match="free VRAM"):
        hardware.ace_profile(gpu(), "quality")
    with pytest.raises(ValueError, match="close other"):
        hardware.ace_profile(gpu(24576, 3000))
    with pytest.raises(ValueError, match="Ampere"):
        hardware.ace_profile(gpu(capability=7.5))


def test_installer_checks_architecture_and_driver_without_model_imports():
    assert hardware.cuda128_supported(gpu(capability=12.0))
    assert not hardware.cuda128_supported(gpu(driver="552.44"))
    assert hardware.cuda128_supported(gpu(capability=7.5))
    assert not hardware.cuda128_supported(gpu(capability=7.5), ace=True)
    assert not hardware.cuda128_supported({})


def publish(key, python):
    root = model_setup.packs_root() / key
    (root / "models").mkdir(parents=True)
    (root / "models/weights").write_bytes(b"fixture")
    write_json(
        root / "runtime.json",
        {
            "schema": 1,
            "pack": key,
            "python": str(python),
            "model_dir": str(root / "models"),
            "device": model_setup.PACKS[key].get("device", "cpu"),
            "files": [{"file": "models/weights"}],
            "verification": {m: {"offline": True} for m in model_setup.PACKS[key]["models"]},
        },
    )


def test_managed_device_routing_keeps_cpu_and_gpu_independent(tmp_path, monkeypatch):
    monkeypatch.setenv("MUSIC_WORKBENCH_DATA", str(tmp_path / "user"))
    publish("music-tools", sys.executable)
    gpu_python = tmp_path / "gpu-python.exe"
    gpu_python.write_bytes(b"fixture")
    publish("music-tools-cuda", gpu_python)
    registry = ModelRegistry(type("Service", (), {"root": tmp_path})(), Settings())
    spec = registry.spec("crepe-rest")
    assert registry.python(spec) == str(gpu_python)
    assert registry.python(spec, "cuda") == str(gpu_python)
    assert registry.python(spec, "cpu") == sys.executable
    assert registry.describe("crepe-rest")["execution_device"] == "cuda"
    assert registry.describe("crepe-rest", device="cpu")["execution_device"] == "cpu"
    assert "music-tools-cuda" in registry.environment_settings("crepe-rest", "cuda")["model_dir"]
    assert "music-tools-cuda" not in registry.environment_settings("crepe-rest", "cpu")["model_dir"]


def test_device_checks_do_not_reuse_another_devices_health(tmp_path, monkeypatch):
    monkeypatch.setenv("MUSIC_WORKBENCH_DATA", str(tmp_path / "user"))
    registry = ModelRegistry(type("Service", (), {"root": tmp_path})(), Settings())
    called = []

    def probe(model, deep, cancelled, device):
        called.append(device)
        return {"state": "verified", "weights": True, "cuda": device == "cuda"}

    monkeypatch.setattr(registry, "_probe", probe)
    registry.check("crepe-rest", device="cpu")
    registry.require("crepe-rest", device="cuda")
    registry.require("crepe-rest", device="cpu")
    assert called == ["cpu", "cuda"]
