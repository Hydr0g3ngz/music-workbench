import io
import json
import time
import zipfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from pydantic import ValidationError

from music_studio.io import read_json, write_json
from music_studio.studio.arrangement import Arrangement
from music_studio.studio.musical import PROFILES, analyze, key_candidates, transform
from music_studio.ui.server import create_app


def test_sections_key_backward_compatibility_bounds_and_identity():
    assert Arrangement().sections == [] and Arrangement().key == ""
    valid = {
        "key": "D minor",
        "sections": [{"id": "1234567890abcdef", "name": "引子", "start": 0, "end": 16}],
    }
    assert Arrangement.model_validate(valid).sections[0].name == "引子"
    for data in (
        {"key": "H minor"},
        {"bpm": 30, "sections": [{**valid["sections"][0], "end": 301}]},
        {"sections": valid["sections"] * 2},
    ):
        with pytest.raises(ValidationError):
            Arrangement.model_validate(data)


def test_key_estimator_silence_and_transposition():
    assert key_candidates(np.zeros((12, 10))) == []
    for shift in (0, 2, 7):
        chroma = np.tile(np.roll(PROFILES["minor"], shift)[:, None], (1, 10))
        assert (
            key_candidates(chroma)[0]["key"] == ("C", "D", "G")[(0, 2, 7).index(shift)] + " minor"
        )


def test_independent_time_pitch_preserves_source_and_stereo(tmp_path):
    rate = 22050
    t = np.arange(rate * 2) / rate
    signal = 0.15 * np.sin(2 * np.pi * 440 * t)
    source, target = tmp_path / "source.wav", tmp_path / "fitted.wav"
    sf.write(source, np.column_stack([signal, signal * 0.5]), rate, subtype="FLOAT")
    before = source.read_bytes()
    transform(source, target, 1.25, 12)
    audio, actual_rate = sf.read(target, always_2d=True)
    assert actual_rate == rate and audio.shape == (round(len(t) / 1.25), 2)
    np.testing.assert_allclose(audio[:, 0] * 0.5, audio[:, 1], atol=1e-6)
    segment = audio[rate // 4 : rate, 0]
    frequency = np.argmax(np.abs(np.fft.rfft(segment))) * rate / len(segment)
    assert abs(frequency - 880) < 3
    assert source.read_bytes() == before
    silent = tmp_path / "silence.wav"
    sf.write(silent, np.zeros((rate, 2)), rate)
    report = analyze(silent)
    assert report["key"] is None and report["tempo_bpm"] is None


def test_pack_roundtrip_in_fresh_workspace_preserves_audio_mix_and_metadata(tmp_path):
    with TestClient(create_app(tmp_path / "original"), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={"demo": True}).json()
        prefix = "/api/workstation/projects/" + state["id"]
        state["content"].update(
            key="F major",
            sections=[{"id": "1234567890abcdef", "name": "段落 A", "start": 0, "end": 16}],
        )
        state = client.put(
            prefix, json={"revision": state["revision"], "content": state["content"]}
        ).json()
        pack = client.post(prefix + "/pack", json={"revision": state["revision"]})
        assert pack.status_code == 200, pack.text
        raw = client.get(pack.json()["url"]).content
        url = client.post(prefix + "/export/wav", json={"revision": state["revision"]}).json()[
            "url"
        ]
        reference = client.get(url).content
    with TestClient(create_app(tmp_path / "fresh"), base_url="http://127.0.0.1") as client:
        result = client.post(
            "/api/workstation/projects/import-pack", files={"file": ("piece.mwb", raw)}
        )
        assert result.status_code == 201, result.text
        restored = result.json()
        assert restored["id"] != state["id"] and restored["revision"] == 0
        assert restored["content"] == state["content"]
        assert restored["assets"][0]["source_project"] != state["assets"][0]["source_project"]
        url = client.post(
            "/api/workstation/projects/" + restored["id"] + "/export/wav", json={"revision": 0}
        ).json()["url"]
        assert client.get(url).content == reference


def test_pack_rejects_path_traversal_and_corruption_without_creating_projects(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        for kind in ("traversal", "checksum", "duplicate"):
            data = io.BytesIO()
            manifest = {
                "format": "music-workbench-pack",
                "version": 1,
                "content": Arrangement().model_dump(),
                "assets": [],
            }
            with zipfile.ZipFile(data, "w") as archive:
                if kind == "traversal":
                    archive.writestr("../escape.txt", "bad")
                if kind == "checksum":
                    manifest["assets"] = [
                        {
                            "id": "1234567890abcdef",
                            "name": "test",
                            "file": "assets/1234567890abcdef.wav",
                            "sha256": "0" * 64,
                        }
                    ]
                    archive.writestr("assets/1234567890abcdef.wav", b"broken")
                archive.writestr("project.json", json.dumps(manifest))
                if kind == "duplicate":
                    with pytest.warns(UserWarning):
                        archive.writestr("project.json", "{}")
            response = client.post(
                "/api/workstation/projects/import-pack",
                files={"file": ("bad.mwb", data.getvalue())},
            )
            assert response.status_code == 422, response.text
            assert client.get("/api/workstation/projects").json() == []
        assert not (tmp_path / "escape.txt").exists()


@pytest.mark.parametrize(
    "model,ratio,roles",
    [
        ("demucs-four-stems", 1, ("drums", "bass", "vocals", "other")),
        ("time-pitch", 1.25, ("transformed",)),
    ],
)
def test_new_audio_results_publish_adopt_reopen_and_undo(
    tmp_path, monkeypatch, model, ratio, roles
):
    def worker(command, *args, **kwargs):
        request = read_json(Path(command[-1]))
        output = Path(request["output"])
        output.mkdir(exist_ok=True)
        artifacts = []
        for role in roles:
            sf.write(
                output / (role + ".wav"),
                np.zeros((round(sf.info(request["input"]).frames / ratio), 2)),
                44100,
                subtype="FLOAT",
            )
            artifacts.append(
                {"role": role, "kind": "audio", "file": role + ".wav", "mime": "audio/wav"}
            )
        write_json(output / "result.json", {"artifacts": artifacts, "metrics": {"fixture": True}})
        return 0

    monkeypatch.setattr("music_studio.studio.tasks.run_owned", worker)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        monkeypatch.setattr(
            client.app.state.studio.tasks.registry, "require", lambda *a, **k: {"runtime": "base"}
        )
        state = client.post("/api/workstation/projects", json={}).json()
        prefix = "/api/workstation/projects/" + state["id"]
        data = io.BytesIO()
        sf.write(data, np.zeros((44100, 2)), 44100, format="WAV")
        state = client.post(
            prefix + "/import?revision=0", files={"file": ("source.wav", data.getvalue())}
        ).json()
        clip = state["content"]["tracks"][0]["clips"][0]
        clip.update(start=3, offset=0.2, duration=0.6, fade_in=0.05, fade_out=0.1)
        state = client.put(
            prefix, json={"revision": state["revision"], "content": state["content"]}
        ).json()
        task = client.post(
            prefix + "/process",
            json={
                "revision": state["revision"],
                "clip": clip["id"],
                "model": model,
                "time_ratio": ratio,
            },
        ).json()
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            published = client.get(prefix + "/processing").json()[0]
            if published["status"] in ("complete", "failed"):
                break
            time.sleep(0.03)
        assert published["status"] == "complete", published
        result = client.post(
            prefix + "/processing/" + task["id"] + "/adopt-stems",
            json={"revision": state["revision"]},
        )
        assert result.status_code == 200, result.text
        after = result.json()
        assert len(after["content"]["tracks"]) == len(roles)
        adopted = after["content"]["tracks"][0]["clips"][0]
        assert adopted["start"] == 3
        assert adopted["offset"] == 0  # The worker received a cropped, zero-origin input.
        assert published["source_range"]["start"] == pytest.approx(0.2)
        assert adopted["duration"] == pytest.approx(0.6 / ratio)
        assert adopted["fade_in"] == pytest.approx(0.05 / ratio)
        assert client.get(prefix).json() == after
        undone = client.post(prefix + "/history/undo", json={"revision": after["revision"]}).json()
        assert undone["content"] == state["content"]
