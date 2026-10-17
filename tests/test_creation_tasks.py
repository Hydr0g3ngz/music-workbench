import io
import json
import sys
import threading
import time
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from filelock import FileLock

from music_studio.io import read_json, write_json
from music_studio.studio import creation
from music_studio.studio.process import TaskStopped
from music_studio.ui.server import create_app


def wait_for(client, prefix, states):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        task = client.get(prefix + "/generations").json()[0]
        if task["status"] in states:
            return task
        time.sleep(0.025)
    pytest.fail(f"Task stayed {task['status']}: {task}")


@pytest.fixture
def fake_runtime(monkeypatch, tmp_path):
    config = {
        "python": sys.executable,
        "source": str(tmp_path / "source"),
        "checkpoints": str(tmp_path / "weights"),
        "source_revision": creation.SOURCE_REVISION,
        "model_revision": creation.MODEL_REVISION,
    }
    monkeypatch.setattr(creation, "runtime", lambda: config)
    return config


def completed_worker(arguments, log_path, environment, **kwargs):
    request = read_json(Path(arguments[-1]))
    output = log_path.parent / "output"
    output.mkdir()
    # A fixture waveform, never presented as actual model inference.
    samples = np.sin(np.arange(48000) * 2 * np.pi * 220 / 48000) * 0.1
    sf.write(output / "generated.wav", np.column_stack([samples, samples]), 48000)
    write_json(output / "result.json", {"file": "generated.wav", "metrics": {"test": True}})
    assert environment["HF_HUB_OFFLINE"] == "1"
    assert request["parameters"]["seed"] == 42
    assert request["owner_pid"] > 0
    return 0


def test_repaint_candidate_keeps_outside_audio_and_replaces_only_unchanged_source(
    fake_runtime, tmp_path, monkeypatch
):
    def repaint_worker(arguments, log_path, environment, **kwargs):
        request = read_json(Path(arguments[-1]))
        audio, rate = sf.read(request['reference_audio'], dtype='float32', always_2d=True)
        output = log_path.parent / 'output'
        output.mkdir()
        sf.write(output / 'generated.wav', -audio, rate, subtype='FLOAT')
        write_json(output / 'result.json', {'file':'generated.wav','metrics':{'fixture':True}})
        return 0

    monkeypatch.setattr(creation, 'run_owned', repaint_worker)
    with TestClient(create_app(tmp_path), base_url='http://127.0.0.1') as client:
        state = client.post('/api/workstation/projects', json={}).json()
        prefix = '/api/workstation/projects/' + state['id']
        original = np.column_stack([np.sin(np.arange(44100*12)*.01)*.1]*2).astype('float32')
        stream = io.BytesIO()
        sf.write(stream,original,44100,format='WAV',subtype='FLOAT')
        state = client.post(prefix+'/import?revision=0',
                            files={'file':('reference.wav',stream.getvalue())}).json()
        source = state['content']['tracks'][0]['clips'][0]
        response = client.post(prefix+'/generations',json={
            'revision':state['revision'],'prompt':'Airy transition','mode':'repaint',
            'source_clip':source['id'],'repaint_start':4,'repaint_end':8,
        })
        assert response.status_code == 202, response.text
        task=wait_for(client,prefix,{'complete','failed'})
        assert task['status']=='complete',task
        actual,_=sf.read(io.BytesIO(client.get(prefix+'/generations/'+task['id']+'/audio').content),
                         dtype='float32',always_2d=True)
        assert np.array_equal(original[:4*44100],actual[:4*44100])
        assert np.array_equal(original[8*44100:],actual[8*44100:])
        endpoint=prefix+'/generations/'+task['id']+'/adopt'
        adopted=client.post(endpoint,json={'revision':state['revision'],'replace_source':True})
        assert adopted.status_code==200,adopted.text
        adopted=adopted.json()
        replacement=adopted['content']['tracks'][0]['clips'][0]
        assert len(adopted['content']['tracks'])==1
        assert replacement['id']==source['id'] and replacement['asset']!=source['asset']
        undo=client.post(prefix+'/history/undo',json={'revision':adopted['revision']}).json()
        assert undo['content']==state['content']
        undo['content']['tracks'][0]['clips'][0]['start']=1
        changed=client.put(prefix,json={'revision':undo['revision'],'content':undo['content']}).json()
        assert client.post(endpoint,json={'revision':changed['revision'],
                                          'replace_source':True}).status_code==409


def test_blueprint_preview_is_the_queued_model_prompt_and_survives_later_edits(
    fake_runtime, tmp_path, monkeypatch
):
    monkeypatch.setattr(creation, "run_owned", completed_worker)
    lock = FileLock(str(tmp_path / ".studio-tasks.lock"), timeout=0)
    with lock, TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={}).json()
        prefix = f"/api/workstation/projects/{state['id']}"
        state["content"].update(
            blueprint={"brief": "City sunrise", "motif": "Three short notes"},
            sections=[
                {
                    "id": "1234567890abcdef",
                    "name": "Theme",
                    "start": 16,
                    "end": 48,
                    "role": "theme",
                    "energy": 3,
                }
            ],
        )
        state = client.put(prefix, json={"revision": 0, "content": state["content"]}).json()
        payload = {
            "revision": 1,
            "prompt": "Soft jazz piano",
            "use_blueprint": True,
            "section_id": "1234567890abcdef",
            "development": "develop",
        }
        preview = client.post(prefix + "/generation-preview", json=payload).json()
        task = client.post(prefix + "/generations", json=payload).json()
        assert task["parameters"]["prompt"] == preview["prompt"]
        assert task["composition_context"] == preview["context"]
        assert task["user_prompt"] == payload["prompt"]
        state["content"]["blueprint"]["motif"] = "Four long notes"
        state = client.put(prefix, json={"revision": 1, "content": state["content"]}).json()
        assert (
            client.get(prefix + "/generations").json()[0]["composition_context"]
            == (preview["context"])
        )
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        task = wait_for(client, prefix, {"complete", "failed"})
        assert task["status"] == "complete", task
        adopted = client.post(
            f"{prefix}/generations/{task['id']}/adopt",
            json={
                "revision": 2,
                "target_section": True,
            },
        ).json()
        clip = adopted["content"]["tracks"][0]["clips"][0]
        assert clip["start"] == 16 * 60 / adopted["content"]["bpm"]
        assert preview["context"]["sha256"] in clip["origin"]["details"]
        adopted["content"]["sections"][0]["start"] += 4
        changed = client.put(prefix, json={"revision": 3, "content": adopted["content"]}).json()
        assert (
            client.post(
                f"{prefix}/generations/{task['id']}/adopt",
                json={
                    "revision": changed["revision"],
                    "target_section": True,
                },
            ).status_code
            == 409
        )


def test_reference_variation_pins_only_selected_audio_and_keeps_source_unchanged(
    fake_runtime, tmp_path, monkeypatch
):
    monkeypatch.setattr(creation, "run_owned", completed_worker)
    lock = FileLock(str(tmp_path / ".studio-tasks.lock"), timeout=0)
    with lock, TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={}).json()
        prefix = f"/api/workstation/projects/{state['id']}"
        audio = io.BytesIO()
        samples = np.column_stack([np.linspace(-0.1, 0.1, 44100 * 12)] * 2)
        sf.write(audio, samples, 44100, format="WAV", subtype="FLOAT")
        state = client.post(
            prefix + "/import?revision=0", files={"file": ("reference.wav", audio.getvalue())}
        ).json()
        clip = state["content"]["tracks"][0]["clips"][0]
        clip.update(offset=1, duration=10)
        clip["origin"] = {
            "title": "Original reference",
            "author": "Reference creator",
            "license": "CC BY 4.0",
            "source_url": "https://example.com/reference",
            "details": "Original credit. " + "x" * 2800,
        }
        state = client.put(
            prefix, json={"revision": state["revision"], "content": state["content"]}
        ).json()
        payload = {
            "revision": state["revision"],
            "prompt": "A restrained variation",
            "mode": "cover",
            "source_clip": clip["id"],
            "duration": 30,
        }
        preview = client.post(prefix + "/generation-preview", json=payload)
        assert preview.status_code == 200 and preview.json()["duration"] == 10
        response = client.post(prefix + "/generations", json=payload)
        assert response.status_code == 202, response.text
        task = response.json()
        pinned, rate = sf.read(tmp_path / ".creation-tasks" / task["id"] / "reference.wav")
        assert rate == 44100 and len(pinned) == 10 * 44100
        np.testing.assert_allclose(pinned, samples[44100 : 44100 * 11], atol=1e-6)
        assert task["parameters"]["duration"] == 10
        assert task["reference"]["clip"]["origin"]["author"] == "Reference creator"
        assert client.get(prefix).json() == state
        for extra in ({"source_clip": None}, {"source_clip": "../bad"}, {"source_clip": "0" * 16}):
            assert client.post(prefix + "/generations", json={**payload, **extra}).status_code in (
                422,
                404,
            )
        lock.release()
        task = wait_for(client, prefix, {"complete", "failed"})
        assert task["status"] == "complete", task
        adopted = client.post(
            f"{prefix}/generations/{task['id']}/adopt",
            json={"revision": state["revision"]},
        )
        assert adopted.status_code == 200, adopted.text
        origin = adopted.json()["content"]["tracks"][-1]["clips"][0]["origin"]
        assert "Reference creator" in origin["author"]
        assert "CC BY 4.0" in origin["license"]
        assert task["reference"]["sha256"] in origin["details"]
        assert "https://example.com/reference" in origin["details"]
        assert len(origin["details"]) <= 3000


def test_generation_stays_a_draft_until_adopt_and_keeps_provenance(
    fake_runtime, monkeypatch, tmp_path
):
    monkeypatch.setattr(creation, "run_owned", completed_worker)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={"title": "Music"}).json()
        prefix = f"/api/workstation/projects/{state['id']}"
        submitted = client.post(
            prefix + "/generations", json={"revision": 0, "prompt": "Soft jazz piano"}
        )
        assert submitted.status_code == 202, submitted.text
        assert "runtime" not in submitted.json()
        task = wait_for(client, prefix, {"complete", "failed"})
        assert task["status"] == "complete", task
        assert client.get(prefix).json() == state
        assert task["audio"]["sample_rate"] == 44100
        assert task["audio"]["channels"] == 2
        audio_url = f"{prefix}/generations/{task['id']}/audio"
        assert client.get(audio_url).status_code == 200
        adopted = client.post(
            f"{prefix}/generations/{task['id']}/adopt", json={"revision": 0, "at": 1.5}
        )
        assert adopted.status_code == 200, adopted.text
        updated = adopted.json()
        clip = updated["content"]["tracks"][0]["clips"][0]
        assert clip["start"] == 1.5
        assert clip["origin"]["sha256"] == task["sha256"]
        comparison = client.post(
            prefix + "/comparisons",
            json={
                "revision": updated["revision"],
                "a": "clip:" + clip["id"],
                "b": "generation:" + task["id"],
                "duration": 1,
            },
        )
        assert comparison.status_code == 200, comparison.text
        assert comparison.json()["a"]["audio_sha256"] == comparison.json()["b"]["audio_sha256"]
        assert creation.MODEL_REVISION in clip["origin"]["details"]
        assert (
            client.post(
                f"{prefix}/generations/{task['id']}/adopt", json={"revision": 0}
            ).status_code
            == 409
        )
        undone = client.post(prefix + "/history/undo", json={"revision": 1}).json()
        assert undone["content"]["tracks"] == []
        assert client.get(audio_url).status_code == 200
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        assert client.get(prefix + "/generations").json()[0]["status"] == "complete"


def test_queued_cancel_limits_and_restart_recovery(fake_runtime, tmp_path):
    lock = FileLock(str(tmp_path / ".studio-tasks.lock"), timeout=0)
    with lock, TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={}).json()
        prefix = f"/api/workstation/projects/{state['id']}"
        payload = {"revision": 0, "prompt": "Cinematic music"}
        for _ in range(5):
            assert client.post(prefix + "/generations", json=payload).status_code == 202
        assert client.post(prefix + "/generations", json=payload).status_code == 409
        task = client.get(prefix + "/generations").json()[0]
        result = client.post(f"{prefix}/generations/{task['id']}/cancel", json={})
        assert result.json()["status"] == "cancelled"
        assert client.get(f"{prefix}/generations/{task['id']}/audio").status_code == 409
        # Simulate a process which stopped while a task was running.
        studio = client.app.state.studio
        with studio.connection() as db:
            db.execute("UPDATE creation_tasks SET status='running' WHERE status='queued'")
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        recovered = wait_for(client, prefix, {"cancelled", "interrupted"})
        assert recovered["status"] == "cancelled"
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            states = {t["status"] for t in client.get(prefix + "/generations").json()}
            if states == {"cancelled", "interrupted"}:
                break
            time.sleep(0.025)
        assert states == {"cancelled", "interrupted"}


def test_running_cancel_stops_worker_and_never_changes_arrangement(
    fake_runtime, monkeypatch, tmp_path
):
    entered = threading.Event()

    def blocking_worker(*args, cancelled, **kwargs):
        entered.set()
        while not cancelled():
            time.sleep(0.01)
        raise TaskStopped("cancelled")

    monkeypatch.setattr(creation, "run_owned", blocking_worker)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={}).json()
        prefix = f"/api/workstation/projects/{state['id']}"
        task = client.post(
            prefix + "/generations", json={"revision": 0, "prompt": "Jazz trio"}
        ).json()
        assert entered.wait(5)
        client.post(f"{prefix}/generations/{task['id']}/cancel", json={})
        assert wait_for(client, prefix, {"cancelled"})["status"] == "cancelled"
        assert client.get(prefix).json() == state


def test_runtime_errors_and_generation_validation(monkeypatch, tmp_path):
    config = tmp_path / "runtime.json"
    monkeypatch.setenv("MUSIC_STUDIO_ACE_CONFIG", str(config))
    with TestClient(create_app(tmp_path / "work"), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={}).json()
        prefix = f"/api/workstation/projects/{state['id']}"
        assert not client.get("/api/workstation/generation/status").json()["available"]
        assert (
            client.post(
                prefix + "/generations", json={"revision": 0, "prompt": "Jazz piano"}
            ).status_code
            == 503
        )
        config.write_text(json.dumps({"source_revision": "wrong"}), encoding="utf-8")
        assert (
            client.post(
                prefix + "/generations", json={"revision": 0, "prompt": "Jazz piano"}
            ).status_code
            == 503
        )
        config.write_text("[]", encoding="utf-8")
        assert not client.get("/api/workstation/generation/status").json()["available"]
        assert (
            client.post(
                prefix + "/generations", json={"revision": 0, "prompt": "Jazz piano"}
            ).status_code
            == 503
        )
        for change in (
            {"duration": 300},
            {"seed": -1},
            {"prompt": "   "},
            {"instrumental": False},
            {"steps": 50},
        ):
            assert (
                client.post(
                    prefix + "/generations",
                    json={
                        "revision": 0,
                        "prompt": "Jazz piano",
                        **change,
                    },
                ).status_code
                == 422
            )


def test_failed_draft_keeps_resource_diagnostics_and_original_project(
    fake_runtime, monkeypatch, tmp_path
):
    def failing_worker(arguments, log_path, environment, **kwargs):
        output = log_path.parent / "output"
        output.mkdir()
        log_path.write_text("Fixture: CUDA out of memory", encoding="utf-8")
        write_json(
            output / "failure.json",
            {
                "metrics": {
                    "total_seconds": 2.5,
                    "peak_allocated_mib": 3500,
                }
            },
        )
        return 1

    monkeypatch.setattr(creation, "run_owned", failing_worker)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={}).json()
        prefix = f"/api/workstation/projects/{state['id']}"
        assert (
            client.post(
                prefix + "/generations",
                json={
                    "revision": 0,
                    "prompt": "Jazz piano",
                },
            ).status_code
            == 202
        )
        task = wait_for(client, prefix, {"failed"})
        assert task["metrics"]["peak_allocated_mib"] == 3500
        assert "out of memory" in task["error"]
        assert task["worker_sha256"]
        assert client.get(prefix).json() == state
