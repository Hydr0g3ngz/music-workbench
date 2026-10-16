import copy
import io
import json

import mido
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from pydantic import ValidationError

from music_studio.studio.arrangement import Arrangement
from music_studio.ui.server import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as app:
        yield app


def project(client, demo=False):
    response = client.post("/api/workstation/projects", json={"title": "Timing", "demo": demo})
    assert response.status_code == 201
    state = response.json()
    return state, f"/api/workstation/projects/{state['id']}"


def test_timing_persistence_reopen_and_history(client, tmp_path):
    state, prefix = project(client)
    original = copy.deepcopy(state["content"])
    state["content"]["loop"] = {"enabled": True, "start": 8.5, "end": 16.25}
    state["content"]["metronome"] = {"enabled": True, "volume_db": -24, "accent": False}
    changed = client.put(prefix, json={"revision": 0, "content": state["content"]})
    assert changed.status_code == 200
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as reopened:
        assert reopened.get(prefix).json()["content"] == state["content"]
    undone = client.post(prefix + "/history/undo", json={"revision": 1}).json()
    assert undone["content"] == original
    redone = client.post(prefix + "/history/redo", json={"revision": 2}).json()
    assert redone["content"] == state["content"]


@pytest.mark.parametrize(
    "settings",
    [
        {"loop": {"enabled": True, "start": -1, "end": 4}},
        {"loop": {"start": 4, "end": 4}},
        {"loop": {"start": 4, "end": 2}},
        {"loop": {"start": 4, "end": 4.24}},
        {"loop": {"start": 0, "end": 3001}},
        {"bpm": 30, "loop": {"start": 0, "end": 301}},
        {"metronome": {"volume_db": -49}},
        {"metronome": {"volume_db": -5}},
        {"metronome": {"accent": "unknown"}},
        {"loop": {"unknown": 1}},
    ],
)
def test_invalid_timing_does_not_change_session(client, settings):
    state, prefix = project(client)
    content = {**state["content"], **settings}
    result = client.put(prefix, json={"revision": 0, "content": content})
    assert result.status_code == 422, result.text
    assert client.get(prefix).json() == state


def test_nonfinite_timing_and_tempo_are_rejected():
    for value in (float("nan"), float("inf"), -float("inf")):
        for data in ({"loop": {"end": value}}, {"metronome": {"volume_db": value}}):
            with pytest.raises(ValidationError):
                Arrangement.model_validate(data)
    # Maximum beat range and the 10-minute boundary both allow equality.
    assert Arrangement(bpm=300, loop={"end": 3000}).loop.end == 3000


def test_legacy_saved_rows_and_history_remain_readable_without_eager_migration(tmp_path):
    app = create_app(tmp_path)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        state, prefix = project(client)
        old = {k: v for k, v in state["content"].items() if k not in ("loop", "metronome")}
        # Simulate a project and undo snapshot written by dev6, before timing fields existed.
        with app.state.studio.transaction() as db:
            db.execute(
                "UPDATE arrangements SET content=?, past=? WHERE id=?",
                (json.dumps(old), json.dumps([old]), state["id"]),
            )
        loaded = client.get(prefix).json()
        assert loaded["content"] == old
        validated = Arrangement.model_validate(loaded["content"])
        assert validated.loop.start == 0 and validated.loop.end == 16
        assert not validated.metronome.enabled
        saved = client.put(prefix, json={"revision": 0, "content": old})
        assert saved.status_code == 200
        assert saved.json()["content"]["loop"] == validated.loop.model_dump()
        undo = client.post(prefix + "/history/undo", json={"revision": 1}).json()
        assert undo["content"] == old


def test_exports_ignore_loop_range_and_metronome(client):
    state, prefix = project(client, demo=True)

    def exports(revision):
        results = {}
        for kind in ("wav", "mid"):
            response = client.post(prefix + "/export/" + kind, json={"revision": revision})
            assert response.status_code == 200, response.text
            results[kind] = client.get(response.json()["url"]).content
        return results

    original = exports(state["revision"])
    state["content"]["loop"] = {"enabled": True, "start": 4, "end": 8}
    state["content"]["metronome"] = {"enabled": True, "volume_db": -6, "accent": True}
    saved = client.put(prefix, json={"revision": state["revision"], "content": state["content"]})
    assert saved.status_code == 200
    updated = exports(saved.json()["revision"])
    assert updated == original
    assert sf.info(io.BytesIO(updated["wav"])).duration > 8 * 60 / state["content"]["bpm"]
    assert mido.MidiFile(file=io.BytesIO(updated["mid"])).length > 8
