import copy

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from music_studio.studio.arrangement import Arrangement
from music_studio.studio.composition import ContextRequest, compile_context
from music_studio.studio.service import StudioError
from music_studio.ui.server import create_app


def state():
    return {
        "id": "1234567890abcdef", "revision": 3,
        "content": Arrangement.model_validate({
            "bpm": 120, "key": "D minor",
            "blueprint": {"brief": "Night becoming morning", "motif": "Three plucked notes"},
            "sections": [
                {"id": "2234567890abcdef", "name": "Theme", "start": 0, "end": 32},
                {"id": "3234567890abcdef", "name": "Return", "start": 32, "end": 64,
                 "role": "return", "energy": 3, "intention": "Thin out the drums"},
            ],
        }).model_dump(),
    }


def test_context_has_stable_provenance_and_uses_stored_intentions_only():
    original = state()
    before = copy.deepcopy(original)
    options = ContextRequest(use_blueprint=True, section_id="3234567890abcdef",
                             development="develop")
    compiled = compile_context(original, "Soft electric piano", options)
    assert compiled == compile_context(original, "Soft electric piano", options)
    assert "Thin out the drums" in compiled["prompt"]
    assert "Three plucked notes" in compiled["prompt"]
    assert "120 BPM" in compiled["prompt"] and "D minor" in compiled["prompt"]
    assert compiled["context"]["section_seconds"] == 16
    assert compiled["context"]["neighbors"]["previous"]["name"] == "Theme"
    original["content"]["blueprint"]["motif"] = "Different motif"
    assert compile_context(original, "Soft electric piano", options)["context"]["sha256"] != (
        compiled["context"]["sha256"]
    )
    assert compiled["context"]["blueprint"] == before["content"]["blueprint"]
    assert compile_context(original, "Manual prompt", ContextRequest()) == {
        "prompt": "Manual prompt", "context": None
    }
    with pytest.raises(StudioError):
        compile_context(original, "Manual prompt", ContextRequest(section_id="3234567890abcdef"))
    with pytest.raises(StudioError):
        compile_context(original, "Manual prompt", ContextRequest(
            use_blueprint=True, section_id="4234567890abcdef"))


def test_optional_intentions_are_validated_and_persist_with_history_and_pack(tmp_path):
    assert Arrangement().blueprint.brief == ""
    for data in ({"blueprint": {"brief": "x" * 321}},
                 {"sections": [{"id": "2234567890abcdef", "name": "bad", "start": 0,
                                "end": 4, "energy": 6}]}):
        with pytest.raises(ValidationError):
            Arrangement.model_validate(data)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        created = client.post("/api/workstation/projects", json={}).json()
        prefix = "/api/workstation/projects/" + created["id"]
        saved = client.put(prefix, json={"revision": 0, "content": state()["content"]}).json()
        preview = client.post(prefix + "/generation-preview", json={
            "revision": 1, "prompt": "Soft electric piano", "use_blueprint": True,
            "section_id": "3234567890abcdef", "bpm": 99, "key": "F major",
        })
        assert preview.status_code == 200, preview.text
        assert preview.json()["bpm"] == 120 and preview.json()["key"] == "D minor"
        assert client.post(prefix + "/generation-preview", json={
            "revision": 0, "prompt": "Soft piano"}).status_code == 409
        packed = client.post(prefix + "/pack", json={"revision": 1}).json()
        restored = client.post("/api/workstation/projects/import-pack", files={
            "file": ("piece.mwb", client.get(packed["url"]).content)
        }).json()
        assert restored["content"] == saved["content"]
        undone = client.post(prefix + "/history/undo", json={"revision": 1}).json()
        assert undone["content"]["blueprint"]["brief"] == ""
        redone = client.post(prefix + "/history/redo", json={"revision": 2}).json()
        assert redone["content"] == saved["content"]
