"""A recorded take adopts atomically at the chosen position, including retry/history."""

import io

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from music_studio.ui.server import create_app


def take(rate=48000, seconds=0.25):
    signal = np.sin(np.arange(round(rate * seconds)) * 2 * np.pi * 440 / rate) * 0.2
    audio = io.BytesIO()
    sf.write(audio, signal, rate, format="WAV", subtype="PCM_16")
    return audio.getvalue()


def test_recording_position_retry_undo_reopen_and_export(tmp_path):
    raw = take()
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        initial = client.post("/api/workstation/projects", json={"title": "Recorded idea"}).json()
        prefix = f"/api/workstation/projects/{initial['id']}"
        url = prefix + "/import?revision=0&at=1.25&import_id=abcdef0123456789"
        upload = lambda: {"file": ("Take.wav", raw, "audio/wav")}  # noqa: E731
        adopted = client.post(url, files=upload())
        assert adopted.status_code == 200, adopted.text
        state = adopted.json()
        assert state["revision"] == 1
        clip = state["content"]["tracks"][0]["clips"][0]
        assert clip["start"] == 1.25 and clip["offset"] == 0
        assert abs(clip["duration"] - 0.25) < 1 / 44100
        # A retry with the original revision cannot add a second track, even after restart.
        assert client.post(url, files=upload()).json() == state
        changed = client.post(url, files={"file": ("changed.wav", take(seconds=0.5))})
        assert changed.status_code == 409
        exported = client.post(prefix + "/export/wav", json={"revision": 1}).json()
        mixed, rate = sf.read(io.BytesIO(client.get(exported["url"]).content), always_2d=True)
        assert mixed.shape == (round(1.5 * rate), 2)
        np.testing.assert_allclose(mixed[: round(1.25 * rate)], 0, atol=1e-7)
        assert np.max(np.abs(mixed[round(1.25 * rate):])) > 0.05
        undone = client.post(prefix + "/history/undo", json={"revision": 1}).json()
        assert undone["content"]["tracks"] == []
        redone = client.post(prefix + "/history/redo", json={"revision": 2}).json()
        assert redone["content"] == state["content"]
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        reopened = client.get(prefix).json()
        assert reopened["content"] == state["content"]
        assert client.post(url, files=upload()).json() == reopened


def test_invalid_recording_import_preserves_arrangement_and_sources(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={"title": "Keep me"}).json()
        prefix = f"/api/workstation/projects/{state['id']}"
        for query, expected in [
            ("revision=9&at=2", 409),
            ("revision=0&at=-1", 422),
            ("revision=0&at=nan", 422),
            ("revision=0&at=inf", 422),
            ("revision=0&at=600", 422),
            ("revision=0&import_id=invalid", 422),
            ("revision=0&at=599", 422),
        ]:
            response = client.post(
                prefix + "/import?" + query,
                files={"file": ("too-long.wav", take(seconds=2))},
            )
            assert response.status_code == expected, response.text
            assert client.get(prefix).json() == state
