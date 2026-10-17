import io
import time
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from music_studio.io import read_json, sha256, write_json
from music_studio.studio.fitting import FitOptions, plan
from music_studio.studio.service import StudioError
from music_studio.ui.server import create_app


def import_audio(client, prefix, revision, samples, name="source.wav"):
    raw = io.BytesIO()
    sf.write(raw, np.column_stack([samples, samples]), 44100, format="WAV", subtype="FLOAT")
    response = client.post(
        prefix + f"/import?revision={revision}", files={"file": (name, raw.getvalue())}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_constant_tempo_fit_preserves_pickup_and_places_anchor_exactly():
    clip = {"offset": 0.2, "duration": 12}
    options = FitOptions(source_bpm=100, source_anchor=0.7, target_beat=16)
    fitted = plan(clip, 120, options)
    assert fitted["time_ratio"] == 1.2
    assert fitted["start"] + (0.7 - 0.2) / 1.2 == 8
    assert fitted["duration"] == 10 and fitted["offset"] == pytest.approx(0.2 / 1.2)
    half = plan(clip, 120, options.model_copy(update={"source_bpm": 200, "tempo_multiplier": 0.5}))
    assert half["time_ratio"] == fitted["time_ratio"]
    for change in (
        {"source_anchor": 0.1},
        {"source_anchor": 12.2},
        {"target_beat": 0},
        {"source_bpm": 30},
        {"target_beat": 1200},
    ):
        with pytest.raises(StudioError):
            plan(clip, 120, options.model_copy(update=change))
    with pytest.raises(StudioError):
        plan(
            {"offset": 0, "duration": 120, "fade_in": 30},
            60,
            FitOptions(source_bpm=120, source_anchor=0, target_beat=0),
        )


def test_fitted_result_has_fixed_timing_rejects_changed_bpm_and_undoes(tmp_path, monkeypatch):
    def worker(command, *args, **kwargs):
        request = read_json(Path(command[-1]))
        output = Path(request["output"])
        output.mkdir(exist_ok=True)
        # Frame-count fixture; actual phase-vocoder timing is verified in the real browser run.
        sf.write(
            output / "transformed.wav",
            np.zeros((round(44100 * 2 / 1.2), 2)),
            44100,
            subtype="FLOAT",
        )
        write_json(
            output / "result.json",
            {
                "artifacts": [
                    {
                        "role": "transformed",
                        "kind": "audio",
                        "file": "transformed.wav",
                        "mime": "audio/wav",
                    }
                ],
                "metrics": {"fixture": True},
            },
        )
        return 0

    monkeypatch.setattr("music_studio.studio.tasks.run_owned", worker)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        monkeypatch.setattr(
            client.app.state.studio.tasks.registry, "require", lambda *a, **k: {"runtime": "base"}
        )
        state = client.post("/api/workstation/projects", json={}).json()
        prefix = "/api/workstation/projects/" + state["id"]
        state = import_audio(client, prefix, 0, np.zeros(88200))
        clip = state["content"]["tracks"][0]["clips"][0]
        state["content"]["bpm"] = 120
        clip.update(offset=0.1, duration=1.8)
        state = client.put(prefix, json={"revision": 1, "content": state["content"]}).json()
        payload = {
            "revision": 2,
            "clip": clip["id"],
            "model": "time-pitch",
            "fit": {"source_bpm": 100, "source_anchor": 0.4, "target_beat": 8},
        }
        preview = client.post(
            prefix + "/fit-preview", json={k: v for k, v in payload.items() if k != "model"}
        ).json()
        result = client.post(prefix + "/process", json=payload)
        assert result.status_code == 202, result.text
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            task = client.get(prefix + "/processing").json()[0]
            if task["status"] in ("complete", "failed"):
                break
            time.sleep(0.03)
        assert task["status"] == "complete", task
        assert task["fit"] == preview and task["time_ratio"] == 1.2
        route = prefix + "/processing/" + task["id"] + "/adopt-stems"
        assert client.get(prefix).json() == state
        changed = state["content"].copy()
        changed["bpm"] = 125
        state2 = client.put(prefix, json={"revision": 2, "content": changed}).json()
        assert client.post(route, json={"revision": state2["revision"]}).status_code == 409
        restored = client.post(prefix + "/history/undo", json={"revision": 3}).json()
        result = client.post(route, json={"revision": restored["revision"]})
        assert result.status_code == 200, result.text
        fitted = result.json()
        c = fitted["content"]["tracks"][0]["clips"][0]
        assert c["start"] == pytest.approx(3.75)
        assert c["offset"] == pytest.approx(0.1 / 1.2)
        assert c["duration"] == pytest.approx(1.5)
        assert "beat fit" in c["origin"]["details"]
        comparison = client.post(
            prefix + "/comparisons",
            json={
                "revision": fitted["revision"],
                "a": "clip:" + c["id"],
                "b": f"processing:{task['id']}:{task['artifacts'][0]['id']}",
                "duration": 1,
            },
        )
        assert comparison.status_code == 200, comparison.text
        assert comparison.json()["duration"] == 1
        assert comparison.json()["a"]["audio_sha256"] == comparison.json()["b"]["audio_sha256"]
        undone = client.post(prefix + "/history/undo", json={"revision": fitted["revision"]}).json()
        assert undone["content"] == state["content"]


def test_equal_windows_lufs_attenuation_cache_and_cross_project_isolation(tmp_path):
    samples = 0.2 * np.sin(2 * np.pi * 440 * np.arange(44100 * 4) / 44100)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={}).json()
        prefix = "/api/workstation/projects/" + state["id"]
        state = import_audio(client, prefix, 0, samples, "loud.wav")
        state = import_audio(client, prefix, 1, samples / 4, "soft.wav")
        a, b = [t["clips"][0] for t in state["content"]["tracks"]]
        a.update(offset=0.3, duration=3)
        state = client.put(prefix, json={"revision": 2, "content": state["content"]}).json()
        payload = {
            "revision": 3,
            "a": "clip:" + a["id"],
            "b": "clip:" + b["id"],
            "a_offset": 0.2,
            "b_offset": 0.5,
            "duration": 12,
        }
        response = client.post(prefix + "/comparisons", json=payload)
        assert response.status_code == 200, response.text
        comparison = response.json()
        assert comparison["duration"] == 2.8  # remaining A trim determines common window
        assert comparison["matching_available"]
        # libebur128's histogram bins slightly quantize the level difference.
        assert comparison["a"]["matched_gain"] == pytest.approx(0.25, abs=0.002)
        assert comparison["b"]["matched_gain"] == 1
        for side in ("a", "b"):
            audio = client.get(comparison[side]["url"])
            values, rate = sf.read(io.BytesIO(audio.content))
            assert len(values) == 123480 and rate == 44100
        # A's offset combines the trim start and manual preview offset.
        assert comparison["a"]["offset_frames"] == 22050
        assert client.post(prefix + "/comparisons", json=payload).json() == comparison
        assert client.get(prefix).json() == state
        assert (
            client.post(prefix + "/comparisons", json={**payload, "revision": 0}).status_code == 409
        )
        assert (
            client.post(prefix + "/comparisons", json={**payload, "a_offset": 4}).status_code == 422
        )
        other = client.post("/api/workstation/projects", json={}).json()
        other_prefix = "/api/workstation/projects/" + other["id"]
        assert (
            client.post(other_prefix + "/comparisons", json={**payload, "revision": 0}).status_code
            == 404
        )
        assert (
            client.get(comparison["a"]["url"].replace(state["id"], other["id"])).status_code == 404
        )
        assert (
            client.post(prefix + "/comparisons", json={**payload, "a": "../bad"}).status_code == 422
        )
        path = tmp_path / ".workstation-comparisons" / state["id"] / comparison["id"] / "a.wav"
        path.write_bytes(b"corrupt")
        assert client.get(comparison["a"]["url"]).status_code == 409


def test_silence_falls_back_to_raw_and_peak_headroom_never_amplifies(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={}).json()
        prefix = "/api/workstation/projects/" + state["id"]
        sine = np.sin(2 * np.pi * 200 * np.arange(44100) / 44100) * 1.1
        state = import_audio(client, prefix, 0, sine)
        state = import_audio(client, prefix, 1, np.zeros(44100))
        a, b = ["clip:" + t["clips"][0]["id"] for t in state["content"]["tracks"]]
        payload = {"revision": 2, "a": a, "b": b, "duration": 1}
        raw = client.post(prefix + "/comparisons", json=payload).json()
        assert not raw["matching_available"] and raw["a"]["matched_gain"] == 1
        matched = client.post(prefix + "/comparisons", json={**payload, "b": a}).json()
        assert matched["matching_available"]
        assert matched["a"]["gain_db"] < 0 and matched["a"]["matched_gain"] < 1
        assert matched["a"]["measurement"]["true_peak_dbtp"] + matched["a"]["gain_db"] <= -1
        # Preview computation never mutates the imported source.
        assert (
            sha256(
                client.app.state.studio.asset_path(state["assets"][0]["source_project"], "source")
            )
            == matched["a"]["sha256"]
        )
