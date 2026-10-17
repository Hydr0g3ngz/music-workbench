import sys
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from music_studio.config import Settings
from music_studio.io import read_json, sha256, write_json
from music_studio.studio import ai_setup, model_setup
from music_studio.studio.process import TaskStopped
from music_studio.studio.registry import ModelRegistry
from music_studio.studio.service import StudioError
from music_studio.ui.server import create_app


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MUSIC_WORKBENCH_DATA", str(tmp_path / "user"))
    return tmp_path


def installed(pack):
    root = model_setup.packs_root() / pack
    weights = root / "models/checkpoint.bin"
    weights.parent.mkdir(parents=True, exist_ok=True)
    weights.write_bytes(b"fixture-checkpoint-not-a-real-model")
    value = {
        "schema": 1,
        "pack": pack,
        "python": sys.executable,
        "model_dir": str(weights.parent),
        "files": [{"file": "models/checkpoint.bin", "sha256": sha256(weights)}],
        "verification": {key: {"offline": True} for key in model_setup.PACKS[pack]["models"]},
    }
    write_json(root / "runtime.json", value)
    return root, weights, value


def registry(tmp_path, settings=None):
    service = type("Service", (), {"root": tmp_path})()
    return ModelRegistry(service, settings)


def test_auto_discovery_uses_private_weights_and_preserves_explicit_runtime(isolated):
    root, weights, value = installed("music-tools")
    found = registry(isolated)
    spec = found.spec("crepe-rest")
    assert found.describe("crepe-rest")["runnable"]
    assert found.health == {}  # Opening the model list never launches native imports.
    assert found.python(spec) == sys.executable
    assert found.environment_settings("crepe-rest") == {"model_dir": value["model_dir"]}
    explicit = registry(isolated, Settings(inference_python=str(isolated / "manual-python.exe")))
    assert explicit.python(spec) == str(isolated / "manual-python.exe")
    assert explicit.environment_settings("crepe-rest") == {}
    assert model_setup.managed_runtime("qwen3-asr") is None
    weights.unlink()
    with pytest.raises(ValueError, match="checkpoint changed"):
        model_setup.verify_files(value, root)


def test_deep_check_rejects_corruption_and_ui_cannot_claim_available(isolated):
    root, weights, value = installed("speech-cleanup")
    weights.write_bytes(b"corrupt")
    found = registry(isolated)
    result = found.check("dpdfnet2-48k")
    assert not result["runnable"]
    assert "checkpoint changed" in result["health"]["error"]
    manager = model_setup.ModelSetup(found)
    try:
        assert not manager.describe("speech-cleanup")["installed"]
        with pytest.raises(StudioError, match="AI setup"):
            found.require("dpdfnet2-48k")
    finally:
        manager.close()


def test_unpublished_interrupted_or_deleted_runtime_is_never_available(isolated):
    root = model_setup.packs_root() / "music-tools"
    write_json(root / "setup.json", {"state": "ready"})
    manager = model_setup.ModelSetup(registry(isolated))
    try:
        assert not manager.describe("music-tools")["installed"]
        assert model_setup.managed_runtime("crepe-rest") is None
        _, weights, value = installed("music-tools")
        weights.unlink()
        assert not manager.describe("music-tools")["installed"]
        assert not manager.registry.describe("crepe-rest")["runnable"]
        _, _, value = installed("music-tools")
        value["python"] = str(isolated / "removed/python.exe")
        write_json(root / "runtime.json", value)
        assert not manager.describe("music-tools")["installed"]
        assert model_setup.managed_runtime("crepe-rest") is None
    finally:
        manager.close()


def test_manifest_cannot_escape_tool_root(isolated):
    outside = isolated / "outside.bin"
    outside.write_bytes(b"outside")
    with pytest.raises(ValueError, match="checkpoint changed"):
        model_setup.verify_files(
            {"files": [{"file": "../outside.bin", "sha256": sha256(outside)}]}, isolated / "tools"
        )


def test_embedded_runtime_binds_current_app_after_its_private_dependencies(isolated):
    pth = isolated / "python312._pth"
    pth.write_text("stale-app-location", encoding="utf-8")
    model_setup.bind_app(isolated / "python.exe")
    lines = pth.read_text(encoding="utf-8").splitlines()
    assert lines.index("Lib/site-packages") < lines.index(
        str(Path(model_setup.__file__).parents[2])
    )
    assert "stale-app-location" not in lines


def test_pack_api_cancel_cross_window_and_failure_never_publishes_runtime(isolated, monkeypatch):
    monkeypatch.setattr(
        model_setup,
        "preflight",
        lambda root, pack: {
            "supported": True,
            "reasons": [],
            "directory": str(root),
        },
    )
    entered, finished = threading.Event(), threading.Event()

    def waiting(command, log, env, *, cancelled, timeout):
        assert command[command.index("--pack") + 1] == "speech-cleanup"
        entered.set()
        while not finished.wait(0.01):
            if cancelled():
                raise TaskStopped()
        return 1

    monkeypatch.setattr(ai_setup, "run_owned", waiting)
    app = create_app(isolated / "projects")
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert len(client.get("/api/workstation/model-setup").json()) == 5
        assert client.post("/api/workstation/model-setup/not-a-pack/start").status_code == 404
        response = client.post("/api/workstation/model-setup/speech-cleanup/start")
        assert response.status_code == 200
        assert entered.wait(2)
        second = model_setup.ModelSetup(app.state.studio.tasks.registry)
        try:
            with pytest.raises(StudioError, match="another window"):
                second.get("speech-cleanup").start()
            second.get("speech-cleanup").cancel()
            # close joins the original worker when the app lifespan exits.
        finally:
            second.close()
    assert read_json(model_setup.packs_root() / "speech-cleanup/setup.json")["state"] == "cancelled"
    assert not (model_setup.packs_root() / "speech-cleanup/runtime.json").exists()


def test_failed_offline_inference_keeps_last_published_manifest(isolated, monkeypatch):
    from music_studio.studio import cleanup
    from music_studio.studio import model_install_worker as worker

    root, _, previous = installed("speech-cleanup")
    monkeypatch.setattr(worker, "prepare_python", lambda root, cache: (Path(sys.executable), {}))
    monkeypatch.setattr(cleanup, "download", lambda models, key: root / "models/checkpoint.bin")

    def fail_verification(python, *args, **kwargs):
        if "music_studio.studio.model_verify" in args:
            raise RuntimeError("offline inference failed")

    monkeypatch.setattr(worker.boot, "run", fail_verification)
    with pytest.raises(RuntimeError, match="offline inference failed"):
        worker.install("speech-cleanup", root)
    assert read_json(root / "runtime.json") == previous
