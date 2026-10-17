import io

import mido
import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from music_studio.ui.server import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as app:
        yield app


def create(client, demo=False):
    response = client.post("/api/workstation/projects", json={"title": "Session", "demo": demo})
    assert response.status_code == 201, response.text
    return response.json()


def save(client, state):
    response = client.put(
        f"/api/workstation/projects/{state['id']}",
        json={
            "revision": state["revision"],
            "content": state["content"],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_main_workstation_passes_model_controls_to_task_queue(client, monkeypatch):
    state = create(client, True)
    clip = next(c for t in state["content"]["tracks"] for c in t["clips"] if c["asset"])
    calls = []

    def submit(project, request):
        calls.append((project, request))
        return {"id": f"{len(calls):016x}", "status": "queued"}

    monkeypatch.setattr(client.app.state.studio.tasks, "submit", submit)
    response = client.post(
        f"/api/workstation/projects/{state['id']}/process",
        json={
            "revision": state["revision"],
            "clip": clip["id"],
            "model": "dpdfnet2-48k",
            "device": "cpu",
            "language": "zh",
            "strength": 0.35,
        },
    )
    assert response.status_code == 202, response.text
    assert len(calls) == 1
    task = calls[0][1]
    assert task.device == "cpu" and task.language == "zh" and task.strength == 0.35
    assert task.asset != "current"  # Always use the selected clip's original asset.
    response = client.post(
        f"/api/workstation/projects/{state['id']}/process",
        json={
            "revision": state["revision"],
            "clip": clip["id"],
            "model": "qwen3-asr",
            "alignment": "qwen",
            "device": "cuda",
        },
    )
    assert response.status_code == 202, response.text
    assert calls[-1][1].alignment == "qwen"
    response = client.post(
        f"/api/workstation/projects/{state['id']}/process",
        json={
            "revision": state["revision"],
            "clip": clip["id"],
            "model": "crepe-rest",
            "device": "cuda",
            "strength": 2,
        },
    )
    assert response.status_code == 422
    assert len(calls) == 2


def test_demo_real_audio_midi_export_and_reopen(client, tmp_path):
    state = create(client, True)
    prefix = f"/api/workstation/projects/{state['id']}"
    assert len(state["content"]["tracks"]) == 4
    assert len(state["assets"]) == 1
    assert state["content"]["title"] == "Session"
    for kind in ("wav", "mid"):
        export = client.post(prefix + "/export/" + kind, json={"revision": state["revision"]})
        assert export.status_code == 200, export.text
        data = client.get(export.json()["url"]).content
        if kind == "wav":
            audio, rate = sf.read(io.BytesIO(data), always_2d=True)
            assert rate == 44100 and audio.shape == (784000, 2)
            assert 0.01 < np.max(np.abs(audio)) < 1
        else:
            midi = mido.MidiFile(file=io.BytesIO(data))
            assert len(midi.tracks) == 4
            assert sum(m.type == "note_on" for t in midi.tracks for m in t) > 100
    state["content"]["tracks"][1]["clips"][0]["start"] = 1.25
    updated = save(client, state)
    assert updated["revision"] == state["revision"] + 1
    # A separate application instance reads the persisted arrangement.
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as reopened:
        assert reopened.get(prefix).json()["content"] == updated["content"]


def test_unequal_rates_offsets_gain_pan_solo_and_source_preservation(client):
    state = create(client)
    prefix = f"/api/workstation/projects/{state['id']}"
    for index, rate in enumerate((22050, 48000, 44100)):
        signal = np.full((int(rate * (1 + index * 0.25)), 2), 0.1 * (index + 1))
        audio = io.BytesIO()
        sf.write(audio, signal, rate, format="WAV", subtype="FLOAT")
        result = client.post(
            prefix + f"/import?revision={state['revision']}",
            files={"file": (f"source{index}.wav", audio.getvalue())},
        )
        assert result.status_code == 200, result.text
        state = result.json()
    originals = {a["id"]: client.get(prefix + "/audio/" + a["id"]).content for a in state["assets"]}
    tracks = state["content"]["tracks"]
    tracks[0]["clips"][0].update(start=0.1, offset=0.2, duration=0.4)
    tracks[0].update(gain_db=-6.020599913, pan=1)
    tracks[1]["mute"] = True
    tracks[2]["clips"][0].update(start=0.8, duration=0.2)
    state["content"]["master_db"] = 0
    state = save(client, state)
    export = client.post(prefix + "/export/wav", json={"revision": state["revision"]}).json()
    mixed, rate = sf.read(io.BytesIO(client.get(export["url"]).content), always_2d=True)
    # Muted tracks still determine the arrangement's exported time range.
    assert len(mixed) == round(1.25 * rate)
    np.testing.assert_allclose(mixed[round(0.2 * rate)], [0, 0.05], atol=2e-6)
    np.testing.assert_allclose(mixed[round(0.6 * rate)], 0, atol=1e-7)
    np.testing.assert_allclose(mixed[round(0.9 * rate)], 0.3, atol=2e-6)
    state["content"]["tracks"][2]["solo"] = True
    state = save(client, state)
    export = client.post(prefix + "/export/wav", json={"revision": state["revision"]}).json()
    solo = sf.read(io.BytesIO(client.get(export["url"]).content))[0]
    np.testing.assert_allclose(solo[: round(0.8 * rate)], 0, atol=1e-7)
    for identity, original in originals.items():
        assert client.get(prefix + "/audio/" + identity).content == original


def test_history_conflicts_bounds_and_recoverable_delete(client):
    state = create(client, True)
    prefix = f"/api/workstation/projects/{state['id']}"
    previous = state["content"].copy()
    state["content"]["title"] = "Changed"
    changed = save(client, state)
    conflict = client.put(prefix, json={"revision": state["revision"], "content": previous})
    assert conflict.status_code == 409
    undone = client.post(prefix + "/history/undo", json={"revision": changed["revision"]}).json()
    assert undone["content"]["title"] == "Session"
    redone = client.post(prefix + "/history/redo", json={"revision": undone["revision"]}).json()
    assert redone["content"]["title"] == "Changed"
    invalid = redone["content"]
    invalid["tracks"][0]["clips"][0]["offset"] = 599
    assert (
        client.put(prefix, json={"revision": redone["revision"], "content": invalid}).status_code
        == 422
    )
    assert client.get(prefix + "/audio/0000000000000000").status_code == 404
    assert client.post(prefix + "/trash", json={"revision": redone["revision"]}).status_code == 200
    assert client.get(prefix).status_code == 404
    deleted = client.get("/api/workstation/projects?deleted=true").json()[0]
    assert (
        client.post(prefix + "/restore", json={"revision": deleted["revision"]}).status_code == 200
    )
    assert client.get(prefix).json()["content"]["title"] == "Changed"
    assert client.get("/next.html").status_code == 200
    assert client.get("/station.html").status_code == 200


def test_failed_hot_export_leaves_no_partial_download(client, tmp_path):
    state = create(client, True)
    prefix = f"/api/workstation/projects/{state['id']}"
    state["content"]["tracks"][0]["gain_db"] = 12
    state["content"]["master_db"] = 6
    state = save(client, state)
    response = client.post(prefix + "/export/wav", json={"revision": state["revision"]})
    assert response.status_code == 422 and "0 dBFS" in response.text
    assert not list((tmp_path / ".arrangement-exports").glob("*.wav"))


def test_invalid_upload_and_overlapping_fades_are_recoverable(client):
    state = create(client)
    prefix = f"/api/workstation/projects/{state['id']}"
    response = client.post(prefix + "/import?revision=0", files={"file": ("bad.wav", b"invalid")})
    assert response.status_code == 422
    assert client.get(prefix).json()["revision"] == 0
    state = create(client, True)
    state["content"]["tracks"][0]["clips"][0].update(duration=1, fade_in=0.6, fade_out=0.6)
    response = client.put(
        f"/api/workstation/projects/{state['id']}",
        json={
            "revision": state["revision"],
            "content": state["content"],
        },
    )
    assert response.status_code == 422
