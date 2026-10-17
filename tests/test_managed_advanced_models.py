import hashlib
import io
import sys

import pytest

from music_studio.config import Settings
from music_studio.io import write_json
from music_studio.studio import model_assets, model_install_worker, model_setup
from music_studio.studio.registry import ModelRegistry


def publish(root, key, **extra):
    folder = root / "AI/tools" / key
    (folder / "models").mkdir(parents=True)
    (folder / "models/weights").write_bytes(b"fixture")
    value = {
        "schema": 1,
        "pack": key,
        "device": "cuda",
        "python": sys.executable,
        "model_dir": str(folder / "models"),
        "files": [{"file": "models/weights"}],
        "verification": {m: {"offline": True} for m in model_setup.PACKS[key]["models"]},
        **extra,
    }
    write_json(folder / "runtime.json", value)
    return value


def test_advanced_models_discover_without_repository_cwd_and_respect_manual_settings(
    tmp_path, monkeypatch
):
    root = tmp_path / "user"
    monkeypatch.setenv("MUSIC_WORKBENCH_DATA", str(root))
    monkeypatch.delenv("MUSIC_STUDIO_SEPARATION_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)
    separation_config = str(root / "separation-runtime.json")
    publish(root, "vocal-separation", separation_config=separation_config)
    qwen = publish(root, "qwen-transcription", managed_alignment="qwen")
    service = type("Service", (), {"root": tmp_path})()
    registry = ModelRegistry(service, Settings())
    for model in ("mel-band-roformer-kj", "qwen3-asr"):
        assert registry.describe(model)["runnable"]
        assert registry.python(registry.spec(model), "cuda") == sys.executable
        assert registry.python(registry.spec(model), "cpu") == sys.executable
    assert (
        registry.environment_settings("mel-band-roformer-kj")["separation_config"]
        == separation_config
    )
    assert registry.environment_settings("qwen3-asr") == {
        "model_dir": qwen["model_dir"],
        "managed_alignment": "qwen",
    }
    manual = ModelRegistry(service, Settings(lyrics_python=str(tmp_path / "manual.exe")))
    assert manual.managed(manual.spec("qwen3-asr")) is None
    assert manual.environment_settings("qwen3-asr") == {}
    assert manual.python(manual.spec("qwen3-asr")).endswith("manual.exe")
    monkeypatch.setenv("MUSIC_STUDIO_SEPARATION_CONFIG", "explicit.json")
    assert registry.managed(registry.spec("mel-band-roformer-kj")) is None


class Response(io.BytesIO):
    def __init__(self, raw, status=200, headers=None):
        super().__init__(raw)
        self.status = status
        self.headers = headers or {}


def test_model_download_resumes_verified_range_and_rejects_corruption(tmp_path, monkeypatch):
    raw = b"fixed-official-checkpoint"
    path = tmp_path / "model.safetensors"
    path.with_suffix(".safetensors.download").write_bytes(raw[:6])
    calls = []

    def fetch(request, **kwargs):
        calls.append(request.get_header("Range"))
        return Response(raw[6:], 206, {"Content-Range": f"bytes 6-{len(raw) - 1}/{len(raw)}"})

    monkeypatch.setattr(model_assets.urllib.request, "urlopen", fetch)
    model_assets.download_file(
        "https://example.test/pinned", path, len(raw), hashlib.sha256(raw).hexdigest()
    )
    assert path.read_bytes() == raw and calls == ["bytes=6-"]
    # Invalid cached data must not be accepted merely because its size is correct.
    path.write_bytes(b"x" * len(raw))
    monkeypatch.setattr(model_assets.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        model_assets.urllib.request, "urlopen", lambda *a, **k: Response(b"x" * len(raw))
    )
    with pytest.raises(ValueError, match="checksum"):
        model_assets.download_file(
            "https://example.test/pinned", path, len(raw), hashlib.sha256(raw).hexdigest()
        )
    assert path.read_bytes() != raw


def test_small_model_files_check_git_blob_identity(tmp_path, monkeypatch):
    raw = b'{"model":"fixture"}'
    expected = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    monkeypatch.setattr(model_assets.urllib.request, "urlopen", lambda *a, **k: Response(raw))
    path = model_assets.download_file(
        "https://example.test/config", tmp_path / "config.json", len(raw), expected, git_blob=True
    )
    assert path.read_bytes() == raw


def test_qwen_bf16_setup_requires_ampere_and_eight_gb(tmp_path, monkeypatch):
    monkeypatch.setattr(model_setup.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(
        "music_studio.studio.hardware.nvidia_gpus",
        lambda: {"gpus": [{"memory_mib": 8188, "capability": 7.5, "driver": "591.74"}]},
    )
    assert (
        "cuda-compatibility" not in model_setup.preflight(tmp_path, "vocal-separation")["reasons"]
    )
    assert "cuda-compatibility" in model_setup.preflight(tmp_path, "qwen-transcription")["reasons"]


@pytest.mark.parametrize("pack", ["vocal-separation", "qwen-transcription"])
def test_install_dispatches_advanced_assets_before_offline_verification(
    tmp_path, monkeypatch, pack
):
    root = tmp_path / pack
    python = root / "env/python.exe"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"interpreter")
    monkeypatch.setattr(model_install_worker, "prepare_python", lambda *_: (python, {}))
    monkeypatch.setattr(model_install_worker, "windows_wheel", lambda *a, **k: "fixture.whl")
    calls = []

    def asset(name):
        calls.append(name)
        path = root / "models" / name
        path.write_bytes(name.encode())
        return path

    monkeypatch.setattr(
        model_assets,
        "roformer_assets",
        lambda *_: ([asset("roformer")], {"separation_config": "fixture.json"}),
    )
    monkeypatch.setattr(model_assets, "lyric_snapshot", lambda name, _: [asset(name)])

    def run(*args, **kwargs):
        if "music_studio.studio.model_verify" in args:
            assert calls == (["roformer"] if pack == "vocal-separation" else ["qwen", "aligner"])
            assert not (root / "runtime.json").exists()
            assert kwargs["env"]["HF_HUB_OFFLINE"] == "1"
            write_json(
                root / "verification/report.json",
                {m: {} for m in model_setup.PACKS[pack]["models"]},
            )

    monkeypatch.setattr(model_install_worker.boot, "run", run)
    model_install_worker.install(pack, root)
    import json

    runtime = json.loads((root / "runtime.json").read_text())
    assert len(runtime["files"]) == len(calls)
    assert runtime["pack"] == pack
    if pack == "qwen-transcription":
        assert runtime["managed_alignment"] == "qwen"
