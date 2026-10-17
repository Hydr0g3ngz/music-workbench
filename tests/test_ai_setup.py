import threading
import zipfile

import pytest

from music_studio.io import read_json, write_json
from music_studio.studio import ai_setup
from music_studio.studio.ai_install_worker import unpack
from music_studio.studio.process import TaskStopped
from music_studio.studio.service import StudioError


def test_legacy_and_explicit_configs_win_without_overwriting_managed_ai(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MUSIC_WORKBENCH_DATA", str(tmp_path / "user"))
    monkeypatch.delenv("MUSIC_STUDIO_ACE_CONFIG", raising=False)
    assert ai_setup.config_path() == tmp_path / "user/AI/acestep-runtime.json"
    legacy = tmp_path / ".artifacts/acestep-runtime.json"
    write_json(legacy, {"existing": True})
    assert ai_setup.config_path() == legacy
    monkeypatch.setenv("MUSIC_STUDIO_ACE_CONFIG", str(tmp_path / "explicit.json"))
    assert ai_setup.config_path() == tmp_path / "explicit.json"
    assert read_json(legacy) == {"existing": True}


def test_setup_lock_shared_across_windows_cancel_and_retry_preserve_config(tmp_path, monkeypatch):
    monkeypatch.setattr(ai_setup, "preflight", lambda _: {"supported": True})
    entered, finish = threading.Event(), threading.Event()

    def worker(args, log, env, *, cancelled, timeout):
        entered.set()
        while not finish.wait(0.01):
            if cancelled():
                raise TaskStopped()
        return 0

    monkeypatch.setattr(ai_setup, "run_owned", worker)
    config = tmp_path / "acestep-runtime.json"
    write_json(config, {"old": "working"})
    a = ai_setup.AISetup(tmp_path)
    try:
        a.start()
        assert entered.wait(2)
        b = ai_setup.AISetup(tmp_path)
        assert b.status()["state"] == "installing"
        with pytest.raises(StudioError, match="another window"):
            b.start()
        # Closing an observing window must not cancel the actual owner's task.
        b.close()
        assert a.status()["state"] == "installing"
        b.cancel()
        a.thread.join(3)
        assert a.status()["state"] == "cancelled"
        assert read_json(config) == {"old": "working"}
        finish.set()
        a.start()
        a.thread.join(3)
        assert a.status()["state"] == "ready"
        assert not (tmp_path / "cancel.request").exists()
    finally:
        a.close()


def test_abandoned_install_recovers_and_failures_never_claim_ready(tmp_path, monkeypatch):
    write_json(tmp_path / "setup.json", {"state": "installing"})
    setup = ai_setup.AISetup(tmp_path)
    assert setup.status()["state"] == "interrupted"
    monkeypatch.setattr(ai_setup, "preflight", lambda _: {"supported": True})

    def failed(*args, **kwargs):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr(ai_setup, "run_owned", failed)
    setup.start()
    setup.thread.join(3)
    assert setup.status()["state"] == "failed"
    assert "network unavailable" in setup.status()["error"]
    assert not (tmp_path / "acestep-runtime.json").exists()


def test_unsupported_hardware_does_not_start_install(tmp_path, monkeypatch):
    setup = ai_setup.AISetup(tmp_path)
    monkeypatch.setattr(
        ai_setup, "preflight", lambda _: {"supported": False, "reasons": ["nvidia-8gb"]}
    )
    with pytest.raises(StudioError, match="nvidia-8gb"):
        setup.start()
    assert setup.thread is None


def test_runtime_archive_rejects_escape_before_extracting(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as pack:
        pack.writestr("../outside.txt", "bad")
    with pytest.raises(ValueError, match="Invalid"):
        unpack(archive, tmp_path / "runtime")
    assert not (tmp_path / "outside.txt").exists()


def test_setup_parent_loss_stops_only_its_active_child(monkeypatch):
    from music_studio.studio import ai_install_worker as worker
    from music_studio.studio import task_worker

    child, stopped = object(), []
    monkeypatch.setattr(worker, "active_child", child)
    monkeypatch.setattr(task_worker, "owner_alive", lambda _: False)
    monkeypatch.setattr(worker, "stop_owned_process", stopped.append)

    def exited(code):
        raise SystemExit(code)

    monkeypatch.setattr(worker.os, "_exit", exited)
    with pytest.raises(SystemExit) as failure:
        worker.watch_backend(12345)
    assert failure.value.code == 130
    assert stopped == [child]
