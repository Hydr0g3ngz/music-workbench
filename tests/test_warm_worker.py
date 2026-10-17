"""Real process lifecycle checks with a tiny inference fixture, without model weights."""

import os
import sys
import threading
import time

import pytest

from music_studio.io import read_json, write_json
from music_studio.studio.process import TaskStopped
from music_studio.studio.registry import child_environment
from music_studio.studio.warm_worker import WarmWorker


@pytest.fixture
def host(tmp_path, monkeypatch):
    import music_studio.studio.warm_worker as module

    script = tmp_path / "fixture_host.py"
    script.write_text(
        """
import os, sys, time
from pathlib import Path
from music_studio.io import write_json
from music_studio.inference_cache import inference_model, cache_hits
from music_studio.studio import task_worker

def execute(request):
    before = cache_hits()
    inference_model(("fixture",), object)
    time.sleep(request["settings"].get("delay", 0))
    output = Path(request["output"])
    write_json(output / "fixture.json", {"pid": os.getpid()})
    write_json(output / "result.json", {
        "artifacts": [{"role": "fixture", "kind": "json", "file": "fixture.json",
                       "mime": "application/json"}],
        "metrics": {"worker_pid": os.getpid(), "model_reused": cache_hits() > before},
    })

task_worker.execute = execute
task_worker.serve(int(sys.argv[1]))
""",
        encoding="utf-8",
    )
    original = module.subprocess.Popen

    def launch(arguments, **kwargs):
        return original([sys.executable, str(script), arguments[-1]], **kwargs)

    monkeypatch.setattr(module.subprocess, "Popen", launch)
    worker = WarmWorker(sys.executable, child_environment(str(tmp_path)), tmp_path, "fixture")
    yield worker
    worker.close()


def task(tmp_path, number, model="demucs-htdemucs", **settings):
    directory = tmp_path / str(number)
    request = directory / "request.json"
    write_json(
        request,
        {
            "model": model,
            "settings": settings,
            "output": str(directory / "output"),
            "owner_pid": os.getpid(),
        },
    )
    return request


def test_serial_worker_reuses_one_model_and_refuses_profile_changes(host, tmp_path):
    a, b = task(tmp_path, 1), task(tmp_path, 2)
    assert host.run(a, cancelled=lambda: False) == 0
    assert host.run(b, cancelled=lambda: False) == 0
    first, second = [read_json(p.parent / "output/result.json")["metrics"] for p in (a, b)]
    assert first["worker_pid"] == second["worker_pid"]
    assert first["model_reused"] is False and second["model_reused"] is True
    assert host.run(task(tmp_path, 3, model="whisper-small"), cancelled=lambda: False) == 1
    assert host.process.poll() is not None
    assert not (tmp_path / "3/output/result.json").exists()


@pytest.mark.parametrize("reason", ["cancel", "timeout"])
def test_cancel_or_timeout_stops_host_and_publishes_no_output(host, tmp_path, reason):
    request = task(tmp_path, 1, delay=20)
    started = time.monotonic()
    with pytest.raises(TaskStopped if reason == "cancel" else TimeoutError):
        host.run(
            request,
            cancelled=lambda: reason == "cancel" and time.monotonic() - started > 0.8,
            timeout=0.8 if reason == "timeout" else 10,
        )
    assert host.process.poll() is not None
    assert not (request.parent / "output/result.json").exists()


@pytest.mark.parametrize("reason", ["generation", "idle", "shutdown"])
def test_queue_retires_a_resident_worker(tmp_path, monkeypatch, reason):
    # The queue must release its cross-process lock and resident model before ACE starts.
    from music_studio.studio.service import StudioService

    service = StudioService(tmp_path)
    closed = threading.Event()

    class Resident:
        last_used = time.monotonic()

        def close(self):
            closed.set()

    try:
        if reason == "generation":
            with service.transaction() as db:
                db.execute("CREATE TABLE creation_tasks (status TEXT)")
                db.execute("INSERT INTO creation_tasks VALUES ('queued')")
        if reason == "idle":
            monkeypatch.setattr("music_studio.studio.tasks.IDLE_SECONDS", 0.1)
        service.tasks.worker = Resident()
        service.tasks.wake.set()
        if reason == "shutdown":
            service.close()
        assert closed.wait(3)
        assert service.tasks.worker is None
    finally:
        service.close()
