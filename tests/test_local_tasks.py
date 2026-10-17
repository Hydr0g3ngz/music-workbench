import json
import os
import sys
import threading
import time
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from filelock import FileLock

from music_studio.io import read_json, sha256, write_json
from music_studio.schema import Lyrics
from music_studio.studio.models import LocalTaskRequest, PreviewRequest, TranscriptPatch
from music_studio.studio.process import TaskStopped, run_owned
from music_studio.studio.service import StudioError, StudioService
from music_studio.studio.task_worker import owner_alive, synthesize_notes
from music_studio.studio.tools import ToolCatalog
from music_studio.studio.transcripts import correct
from music_studio.ui.server import create_app


def wait_for(check, timeout=20):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        result = check()
        if result:
            return result
        time.sleep(0.05)
    raise AssertionError("Local task did not reach its expected state")


@pytest.fixture
def local_project(tmp_path, monkeypatch):
    monkeypatch.setenv("MUSIC_WORKBENCH_DATA", str(tmp_path / "user-data"))
    project = "abcdef1234567890"
    folder = tmp_path / project
    studio = folder / ".studio"
    studio.mkdir(parents=True)
    sf.write(studio / "source.wav", np.full((44100, 2), 0.125), 44100, subtype="FLOAT")
    write_json(studio / "source.json", {"file": ".studio/source.wav"})
    write_json(
        folder / "job.json",
        {
            "id": project,
            "title": "Local",
            "status": "ready",
            "filename": "original.wav",
            "created_at": 1,
        },
    )
    service = StudioService(tmp_path)
    yield service, project
    service.close()


def test_real_isolated_task_preserves_input_revision_and_restarts(local_project):
    service, project = local_project
    original = sha256(service.asset_path(project, "source"))
    preview = service.preview(
        project, PreviewRequest(revision=0, operations=[{"type": "gain", "db": -6.020599913}])
    )
    service.adopt(project, preview["id"], 0)
    catalog = ToolCatalog(service, actor="mcp", project=project)
    service.tasks.registry.settings.device = "cpu"
    assert (
        catalog.call("audio_list_models", {"project": project})["models"][0]["health"]["state"]
        == "unchecked"
    )
    job = catalog.call("audio_run_task", {"project": project, "revision": 1, "model": "inspect"})
    assert job["device"] == "cpu"  # Auto respects an explicitly configured CPU runtime.
    # Change the active edit while the queued job retains the exact input it captured.
    service.history(project, 1, "undo")
    done = wait_for(
        lambda: next(
            (
                j
                for j in service.tasks.list(project)
                if j["id"] == job["id"] and j["status"] in ("complete", "failed")
            ),
            None,
        )
    )
    assert done["status"] == "complete", done
    asset = done["artifacts"][0]
    result = catalog.call("audio_read_artifact", {"project": project, "asset": asset["id"]})
    assert result["data"]["peak"] == pytest.approx(0.0625)
    assert done["input_sha256"] == preview["sha256"]
    assert done["metrics"]["device"] == "cpu" and done["metrics"]["torch_peak_mb"] is None
    assert service.session(project)["revision"] == 2
    assert service.session(project)["active"] == "source"
    assert sha256(service.asset_path(project, "source")) == original
    service.close()
    restarted = StudioService(service.root)
    try:
        assert restarted.tasks.get(project, job["id"])["status"] == "complete"
        assert restarted.registered_assets(project)[0]["sha256"] == asset["sha256"]
        with pytest.raises(StudioError):
            restarted.tasks.artifact_path(project, "../../outside")
        with pytest.raises(StudioError):
            catalog.call("audio_run_task", {"project": project, "revision": 0, "model": "inspect"})
    finally:
        restarted.close()


def test_cpu_capabilities_reject_cuda_and_wrong_cleanup_options(local_project):
    service, project = local_project
    with pytest.raises(StudioError, match="uses CPU"):
        service.tasks.submit(project, LocalTaskRequest(revision=0, model="gtcrn", device="cuda"))
    with pytest.raises(StudioError, match="only supported"):
        service.tasks.submit(project, LocalTaskRequest(revision=0, model="inspect", strength=0.5))
    assert service.tasks.list(project) == []


def test_task_range_is_frame_exact_and_old_full_source_tasks_still_map(local_project):
    from pydantic import ValidationError

    from music_studio.studio.task_range import clip_window

    service, project = local_project
    for value in ({"start": 0.3, "end": 0.2}, {"start": float("nan"), "end": 1}):
        with pytest.raises(ValidationError):
            LocalTaskRequest(revision=0, model="inspect", range=value)
    for value in ({"start": 1.1, "end": 1.2}, {"start": 0.2, "end": 2}, {"start": 0, "end": 1e-8}):
        with pytest.raises(StudioError, match="range"):
            service.tasks.submit(
                project, LocalTaskRequest(revision=0, model="inspect", range=value)
            )
    job = service.tasks.submit(
        project,
        LocalTaskRequest(
            revision=0,
            model="inspect",
            range={"start": 0.123456, "end": 0.765432},
        ),
    )
    done = wait_for(
        lambda: (
            r
            if (r := service.tasks.get(project, job["id"]))["status"] in ("complete", "failed")
            else None
        )
    )
    assert done["status"] == "complete", done
    assert done["input_audio"]["frames"] == round(0.765432 * 44100) - round(0.123456 * 44100)
    assert done["source_range"]["source_sha256"] != done["input_sha256"]
    repeated = service.tasks.submit(
        project,
        LocalTaskRequest(revision=0, model="inspect", range={"start": 0.123456, "end": 0.765432}),
    )
    assert repeated["input_sha256"] == done["input_sha256"]
    legacy = {"source_clip": {"offset": 3, "duration": 4}, "stage": "transform", "time_ratio": 2}
    assert clip_window(legacy) == (1.5, 2)
    assert clip_window({**legacy, "source_range": {"start": 3}}) == (0, 2)


@pytest.mark.parametrize("rate,channels", [(48000, 2), (44100, 1)])
def test_task_outputs_must_preserve_rate_and_channels(local_project, monkeypatch, rate, channels):
    service, project = local_project

    def fake_worker(command, *args, **kwargs):
        request = read_json(Path(command[-1]))
        output = Path(request["output"])
        output.mkdir(exist_ok=True)
        sf.write(output / "bad.wav", np.zeros((44100, channels)), rate, subtype="FLOAT")
        write_json(
            output / "result.json",
            {
                "artifacts": [
                    {"role": "bad", "kind": "audio", "file": "bad.wav", "mime": "audio/wav"}
                ],
                "metrics": {"device": "cpu", "seconds": 0.1},
            },
        )
        return 0

    monkeypatch.setattr("music_studio.studio.tasks.run_owned", fake_worker)
    monkeypatch.setattr(service.tasks.registry, "require", lambda *a, **k: {"runtime": "base"})
    job = service.tasks.submit(project, LocalTaskRequest(revision=0, model="inspect"))
    result = wait_for(
        lambda: (
            service.tasks.get(project, job["id"])
            if service.tasks.get(project, job["id"])["status"] in ("failed", "complete")
            else None
        )
    )
    assert result["status"] == "failed"
    assert "timeline" in result["error"]
    assert service.registered_assets(project) == []


def test_queue_cancel_recovery_and_trash_guard(local_project):
    service, project = local_project
    # Hold the real cross-process lock, leaving durable jobs queued for restart.
    with FileLock(str(service.root / ".studio-tasks.lock")):
        first = service.tasks.submit(project, LocalTaskRequest(revision=0, model="inspect"))
        second = service.tasks.submit(project, LocalTaskRequest(revision=0, model="inspect"))
        assert service.tasks.cancel(project, second["id"])["status"] == "cancelled"
        with TestClient(create_app(service.root), base_url="http://127.0.0.1") as client:
            assert client.delete(f"/api/projects/{project}").status_code == 409
        service.close()
    other = StudioService(service.root)
    try:
        done = wait_for(
            lambda: (
                other.tasks.get(project, first["id"])
                if other.tasks.get(project, first["id"])["status"] in ("complete", "failed")
                else None
            )
        )
        assert done["status"] == "complete", done
        assert other.tasks.get(project, second["id"])["status"] == "cancelled"
        # Terminal output registration is not duplicated by another independent client.
        assert len(other.registered_assets(project)) == 1
    finally:
        other.close()


def test_runtime_native_failure_is_not_reported_available(local_project, monkeypatch):
    from music_studio.studio import registry

    service, _ = local_project
    original_runner = run_owned

    def exit_native(arguments, log, environment, **kwargs):
        return original_runner(
            [sys.executable, "-c", "import os; os._exit(139)"], log, environment, **kwargs
        )

    monkeypatch.setattr(registry, "run_owned", exit_native)
    result = service.tasks.registry.check("inspect")
    assert result["health"]["state"] == "failed" and not result["runnable"]
    assert "139" in result["health"]["error"]


def test_analysis_version_switch_cannot_retarget_a_pinned_stem(local_project):
    service, project = local_project
    folder = service.project_dir(project)
    original = folder / "result"
    original.mkdir()
    sf.write(original / "vocal.wav", np.full((44100, 2), 0.1), 44100, subtype="FLOAT")
    write_json(
        original / "project.json",
        {"assets": {"source": "../.studio/source.wav", "vocals": "vocal.wav"}},
    )
    old = service.session(project)["analysis_assets"]["vocals"]
    old_hash = sha256(service.asset_path(project, old))
    version = "1122334455667788"
    fresh = folder / "revisions" / version
    fresh.mkdir(parents=True)
    sf.write(fresh / "vocal.wav", np.full((44100, 2), 0.3), 44100, subtype="FLOAT")
    write_json(
        fresh / "project.json",
        {"assets": {"source": "../../.studio/source.wav", "vocals": "vocal.wav"}},
    )
    job = read_json(folder / "job.json")
    job["current_version"] = version
    write_json(folder / "job.json", job)
    current = service.session(project)["analysis_assets"]["vocals"]
    assert old != current
    assert sha256(service.asset_path(project, old)) == old_hash
    assert sha256(service.asset_path(project, current)) != old_hash
    assert len(service.registered_assets(project)) == 2


def test_restart_recovers_lost_owner_and_models_open_without_a_project(local_project):
    service, project = local_project
    with FileLock(str(service.root / ".studio-tasks.lock")):
        queued = service.tasks.submit(project, LocalTaskRequest(revision=0, model="inspect"))
        with service.transaction() as db:
            db.execute("UPDATE tasks SET status='running' WHERE id=?", (queued["id"],))
        service.close()
    with TestClient(create_app(service.root), base_url="http://127.0.0.1") as client:
        models = client.get("/api/studio/models")
        assert models.status_code == 200
        assert {"demucs-htdemucs", "mel-band-roformer-kj"} <= {m["id"] for m in models.json()}
        assert client.post("/api/studio/models/unknown/check").status_code == 404
        recovered = wait_for(
            lambda: next(
                (
                    j
                    for j in client.get(f"/api/projects/{project}/studio/tasks").json()
                    if j["status"] == "interrupted"
                ),
                None,
            )
        )
        assert recovered["id"] == queued["id"]
        assert client.app.state.studio.session(project)["revision"] == 0
    with TestClient(create_app(service.root / "empty"), base_url="http://127.0.0.1") as client:
        assert client.get("/api/studio/models").status_code == 200
        assert client.get("/api/projects").json() == []


def test_new_task_stems_mix_without_a_classic_analysis(local_project):
    from music_studio.studio.dsp import inspect_audio

    service, project = local_project
    source = service.asset_path(project)
    directory = service.studio_dir(project, "tasks/1122334455667788/output")
    for key, role, gain in (
        ("1111222233334444", "vocals", 0.1),
        ("5555666677778888", "instrumental", 0.025),
    ):
        path = directory / f"{role}.wav"
        sf.write(path, np.full((44100, 2), gain), 44100, subtype="FLOAT")
        record = {
            "id": key,
            "task": "1122334455667788",
            "model": "fixture-stem-pair",
            "kind": "audio",
            "role": role,
            "file": str(path.relative_to(service.project_dir(project))),
            "input_sha256": sha256(source),
            "sha256": sha256(path),
            "audio": inspect_audio(path),
        }
        with service.transaction() as db:
            db.execute(
                "INSERT INTO assets VALUES (?,?,?,?,?,?)",
                (key, project, record["task"], role, "audio", json.dumps(record)),
            )
    state = service.session(project)
    assert state["assets"] == ["source"] and state["analysis_assets"] == {}
    assert len(state["mix_pairs"]) == 1
    pair = state["mix_pairs"][0]
    preview = service.preview(
        project,
        PreviewRequest(
            revision=0,
            operations=[
                {
                    "type": "mix",
                    "tracks": [{"asset": pair["vocals"]}, {"asset": pair["instrumental"]}],
                }
            ],
        ),
    )
    mixed, _ = sf.read(service.asset_path(project, "candidate:" + preview["id"]))
    np.testing.assert_allclose(mixed, sf.read(source)[0], atol=2e-8)


def test_cancel_kills_the_owned_process_tree(tmp_path):
    marker = tmp_path / "child.json"
    # This is a real process tree including Windows' venv proxy when present.
    script = (
        "import json,pathlib,subprocess,sys,time; "
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        "path=pathlib.Path(sys.argv[1]); pending=path.with_suffix('.pending'); "
        "pending.write_text(json.dumps({'child':child.pid})); pending.replace(path); time.sleep(60)"
    )
    stopped = threading.Event()
    failures = []

    def run():
        try:
            run_owned(
                [sys.executable, "-c", script, str(marker)],
                tmp_path / "process.log",
                os.environ.copy(),
                cancelled=stopped.is_set,
                timeout=15,
            )
        except TaskStopped:
            return
        except BaseException as error:
            failures.append(error)

    thread = threading.Thread(target=run)
    thread.start()
    wait_for(marker.is_file)
    child = read_json(marker)["child"]
    stopped.set()
    thread.join(timeout=12)
    assert not thread.is_alive() and not failures

    def exited():
        status = Path(f"/proc/{child}/stat")
        try:
            if os.name != "nt" and status.is_file() and ") Z " in status.read_text():
                return True  # A zombie has exited and owns no model resources.
        except FileNotFoundError:
            return True  # The process was reaped between observation and read.
        return not owner_alive(child)

    wait_for(exited, timeout=5)


def test_immutable_transcript_correction_clears_only_changed_word_times(local_project):
    service, project = local_project
    folder = service.studio_dir(project, "tasks/1234567890abcdef/output")
    original = Lyrics(
        language="en",
        timing_method="native",
        segments=[
            {
                "id": "l0",
                "start": 0,
                "end": 0.5,
                "text": "wrnog",
                "words": [{"id": "w0", "start": 0, "end": 0.4, "text": "wrnog"}],
            },
            {
                "id": "l1",
                "start": 0.5,
                "end": 1,
                "text": "keep",
                "words": [{"id": "w1", "start": 0.6, "end": 0.9, "text": "keep"}],
            },
        ],
    )
    file = folder / "lyrics.json"
    write_json(file, original.model_dump())
    digest = sha256(file)
    asset = {
        "id": "1234567890abcdef",
        "task": "1234567890abcdef",
        "model": "whisper-small",
        "role": "lyrics",
        "kind": "transcript",
        "mime": "application/json",
        "file": str(file.relative_to(service.project_dir(project))),
        "sha256": digest,
        "input_sha256": "0" * 64,
    }
    with service.transaction() as db:
        db.execute(
            "INSERT INTO assets VALUES (?,?,?,?,?,?)",
            (asset["id"], project, asset["task"], "lyrics", "transcript", json.dumps(asset)),
        )
    result = correct(
        service, project, asset["id"], TranscriptPatch(sha256=digest, changes={"l0": "correct"})
    )
    path, record = service.tasks.artifact_path(project, result["asset"])
    changed = read_json(path)
    assert record["parent"] == asset["id"] and record["transcript_revision"] == 1
    assert changed["segments"][0]["text"] == "correct" and changed["segments"][0]["words"] == []
    assert changed["segments"][0]["start"] == 0 and changed["segments"][0]["end"] == 0.5
    assert changed["segments"][1] == original.segments[1].model_dump()
    assert sha256(file) == digest and (path.parent / "lyrics.lrc").read_text().startswith(
        "[00:00.00]correct"
    )
    with pytest.raises(StudioError):
        correct(
            service, project, asset["id"], TranscriptPatch(sha256="0" * 64, changes={"l0": "no"})
        )
    with pytest.raises(StudioError):
        correct(
            service, project, asset["id"], TranscriptPatch(sha256=digest, changes={"unknown": "no"})
        )


def test_rest_decoder_preserves_repeated_notes_and_synthesized_silence(tmp_path):
    from music_studio.backends.melody import stable_notes_from_contour
    from music_studio.schema import Melody

    times = np.arange(200) * 0.01
    frequencies = np.full(len(times), 440.0)
    frequencies[90:98] = np.nan
    scores = np.ones(len(times))
    legacy = stable_notes_from_contour(times, frequencies, scores, 2)
    notes = stable_notes_from_contour(
        times, frequencies, scores, 2, bridge_seconds=0, share_gaps=False
    )
    assert len(legacy) == 1 and len(notes) == 2
    assert notes[1].start - notes[0].end == pytest.approx(0.08)
    path = tmp_path / "notes.wav"
    synthesize_notes(path, Melody(backend="test", notes=notes), 2)
    audio, rate = sf.read(path)
    assert len(audio) == 88200 and rate == 44100
    assert np.max(np.abs(audio[int(0.9 * rate) : int(0.97 * rate)])) == 0
    assert np.max(np.abs(audio[: int(0.8 * rate)])) > 0.1
