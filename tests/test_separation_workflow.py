"""Exercise real task publication and atomic arrangement adoption without model weights."""

import io
import time
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from music_studio.io import read_json, write_json
from music_studio.ui.server import create_app


@pytest.fixture
def workflow(tmp_path, monkeypatch):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        service = client.app.state.studio
        monkeypatch.setattr(service.tasks.registry, "require", lambda *a, **k: {"runtime": "base"})

        def worker(command, *args, **kwargs):
            request = read_json(Path(command[-1]))
            audio, rate = sf.read(request["input"], dtype="float32", always_2d=True)
            output = Path(request["output"])
            output.mkdir(exist_ok=True)
            artifacts = []
            for role, factor in (("vocals", 0.3), ("instrumental", 0.7)):
                sf.write(output / (role + ".wav"), audio * factor, rate, subtype="FLOAT")
                artifacts.append(
                    {"role": role, "kind": "audio", "file": role + ".wav", "mime": "audio/wav"}
                )
            write_json(output / "result.json", {"artifacts": artifacts, "metrics": {"seconds": 0}})
            return 0

        monkeypatch.setattr("music_studio.studio.tasks.run_owned", worker)
        state = client.post("/api/workstation/projects", json={"title": "Aligned stems"}).json()
        base = "/api/workstation/projects/" + state["id"]
        data = io.BytesIO()
        sf.write(
            data,
            np.random.default_rng(9).normal(0, 0.04, (44100, 2)),
            44100,
            format="WAV",
            subtype="FLOAT",
        )
        state = client.post(
            base + "/import?revision=0", files={"file": ("mix.wav", data.getvalue())}
        ).json()
        track = state["content"]["tracks"][0]
        track.update(gain_db=-3, pan=0.25)
        track["clips"][0]["origin"] = {
            "title": "Original mix",
            "author": "Example artist",
            "license": "CC BY 3.0",
            "source_url": "https://example.com/original",
            "details": "Retain attribution",
        }
        track["clips"][0].update(
            start=2.5, offset=0.2, duration=0.6, fade_in=0.05, fade_out=0.1, gain_db=-2
        )
        state = client.put(
            base, json={"revision": state["revision"], "content": state["content"]}
        ).json()
        response = client.post(
            base + "/process",
            json={
                "revision": state["revision"],
                "clip": track["clips"][0]["id"],
                "model": "demucs-htdemucs",
            },
        )
        assert response.status_code == 202, response.text
        task_id = response.json()["id"]
        for _ in range(100):
            tasks = client.get(base + "/processing").json()
            if tasks and tasks[0]["status"] in ("complete", "failed"):
                break
            time.sleep(0.03)
        assert tasks[0]["status"] == "complete", tasks
        yield client, service, base, state, tasks[0], task_id


def test_stem_replacement_is_aligned_atomic_reversible_and_durable(workflow):
    client, service, base, state, task, identity = workflow
    original = client.get(base + "/audio/" + state["assets"][0]["id"]).content
    response = client.post(
        base + f"/processing/{identity}/adopt-stems", json={"revision": state["revision"]}
    )
    assert response.status_code == 200, response.text
    after = response.json()
    assert after["revision"] == state["revision"] + 1
    assert len(after["content"]["tracks"]) == 2
    assert len(after["assets"]) == 3
    for track in after["content"]["tracks"]:
        clip = track["clips"][0]
        assert (clip["start"], clip["offset"], clip["duration"]) == (2.5, 0, 0.6)
        assert (clip["fade_in"], clip["fade_out"], clip["gain_db"]) == (0.05, 0.1, -2)
        assert (track["gain_db"], track["pan"]) == (-3, 0.25)
        assert clip["origin"]["author"] == "Example artist"
        assert clip["origin"]["license"] == "CC BY 3.0"
        assert "model license MIT" in clip["origin"]["details"]
    assert client.get(base + "/audio/" + state["assets"][0]["id"]).content == original
    # Repeated adoption cannot double the mix.
    assert (
        client.post(
            base + f"/processing/{identity}/adopt-stems", json={"revision": after["revision"]}
        ).status_code
        == 409
    )
    undo = client.post(base + "/history/undo", json={"revision": after["revision"]}).json()
    assert undo["content"] == state["content"]
    redo = client.post(base + "/history/redo", json={"revision": undo["revision"]}).json()
    assert redo["content"] == after["content"]
    assert client.get(base + "/processing").json()[0]["source_clip"] == task["source_clip"]


def test_only_trimmed_frames_reach_model_and_comparison_uses_output_origin(workflow):
    client, service, base, state, task, identity = workflow
    directory = service.studio_dir(task["source_project"], f"tasks/{identity}")
    pinned, rate = sf.read(directory / "input.wav", dtype="float32", always_2d=True)
    source, _ = sf.read(
        service.asset_path(task["source_project"], "source"), dtype="float32", always_2d=True
    )
    np.testing.assert_array_equal(pinned, source[8820:35280])
    assert task["source_range"]["start_frame"] == 8820
    assert task["input_audio"]["frames"] == 26460 and rate == 44100
    url = f"/api/projects/{task['source_project']}/studio/tasks/{identity}/input"
    preview = client.get(url)
    assert preview.status_code == 200
    assert sf.info(io.BytesIO(preview.content)).frames == 26460
    assert client.get(url, headers={"Range": "bytes=0-63"}).status_code == 206
    assert client.get(url.replace(task["source_project"], state["id"])).status_code == 404
    # Compare the cropped model output to the corresponding source window.
    artifact = next(a for a in task["artifacts"] if a["role"] == "vocals")
    comparison = client.post(
        base + "/comparisons",
        json={
            "revision": state["revision"],
            "a": "clip:" + task["source_clip"]["id"],
            "b": f"processing:{identity}:{artifact['id']}",
            "duration": 0.5,
        },
    )
    assert comparison.status_code == 200, comparison.text
    assert comparison.json()["a"]["offset_frames"] == 8820
    assert comparison.json()["b"]["offset_frames"] == 0


def test_task_input_preview_refuses_a_changed_snapshot(workflow):
    client, service, _, _, task, identity = workflow
    path = service.tasks.input_path(task["source_project"], identity)
    path.write_bytes(b"changed")
    response = client.get(f"/api/projects/{task['source_project']}/studio/tasks/{identity}/input")
    assert response.status_code == 409


@pytest.mark.parametrize("failure", ["stale", "edited", "tampered", "missing", "track-limit"])
def test_rejected_stem_adoption_never_partially_changes_project(workflow, failure):
    client, service, base, state, task, identity = workflow
    if failure in ("edited", "track-limit"):
        if failure == "edited":
            state["content"]["tracks"][0]["clips"][0]["start"] += 0.5
        else:
            from copy import deepcopy

            template = deepcopy(state["content"]["tracks"][0])
            for i in range(31):
                track = deepcopy(template)
                track["id"] = f"{i + 1:016x}"
                track["clips"] = []
                state["content"]["tracks"].append(track)
        state = client.put(
            base, json={"revision": state["revision"], "content": state["content"]}
        ).json()
    if failure == "tampered":
        path, _ = service.tasks.artifact_path(task["source_project"], task["artifacts"][1]["id"])
        path.write_bytes(b"bad")
    if failure == "missing":
        with service.transaction() as db:
            row = db.execute("SELECT data FROM tasks WHERE id=?", (identity,)).fetchone()
            import json

            data = json.loads(row["data"])
            data["artifacts"] = data["artifacts"][:1]
            db.execute("UPDATE tasks SET data=? WHERE id=?", (json.dumps(data), identity))
    before = client.get(base).json()
    response = client.post(
        base + f"/processing/{identity}/adopt-stems",
        json={"revision": state["revision"] - (failure == "stale")},
    )
    assert response.status_code in (409, 422), response.text
    assert client.get(base).json() == before


def test_optional_separation_missing_is_actionable_and_never_downloads(tmp_path, monkeypatch):
    monkeypatch.setenv("MUSIC_STUDIO_SEPARATION_CONFIG", str(tmp_path / "not-installed.json"))
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        result = client.post("/api/studio/models/mel-band-roformer-kj/check").json()
        assert not result["runnable"]
        assert result["health"]["state"] == "missing"
        assert "AI setup" in result["health"]["error"]


def test_attention_adapter_preserves_upstream_fallback_on_older_torch():
    from types import SimpleNamespace

    from music_studio.studio.separation import prepare_attention

    old = SimpleNamespace(_HAS_SDPA_KERNEL=True, sdpa_kernel=lambda backends: None)
    assert prepare_attention(old) == "legacy-sdpa"
    assert not old._HAS_SDPA_KERNEL
    modern = SimpleNamespace(
        _HAS_SDPA_KERNEL=True, sdpa_kernel=lambda backends, set_priority=False: None
    )
    assert prepare_attention(modern) == "priority-sdpa"
    assert modern._HAS_SDPA_KERNEL
