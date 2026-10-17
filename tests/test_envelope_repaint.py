import io

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from pydantic import ValidationError

from music_studio.studio.arrangement import Clip
from music_studio.studio.envelope import envelope
from music_studio.studio.repaint import splice
from music_studio.ui.server import create_app


def test_curve_interpolates_amplitude_and_rejects_unordered_outside_points():
    clip = Clip(
        id="a" * 16,
        name="curve",
        duration=4,
        volume_points=[{"time": 0, "db": -20}, {"time": 4, "db": 0}],
    )
    assert envelope(np.array([0, 2, 4]), clip).tolist() == pytest.approx([0.1, 0.55, 1])
    for points in ([{"time": 5, "db": 0}], [{"time": 1, "db": 0}, {"time": 1, "db": -2}]):
        with pytest.raises(ValidationError):
            Clip(id="a" * 16, name="curve", duration=4, volume_points=points)


def test_repaint_is_sample_exact_outside_region_and_blends_inside(tmp_path):
    rate = 44100
    rng = np.random.default_rng(42)
    source = (rng.standard_normal((rate * 2, 2)) * 0.05).astype("float32")
    generated = -source
    reference, candidate, output = (tmp_path / x for x in ("ref.wav", "gen.wav", "out.wav"))
    sf.write(reference, source, rate, subtype="FLOAT")
    sf.write(candidate, generated, rate, subtype="FLOAT")
    metrics = splice(reference, candidate, output, 0.5, 1.5, 0.1)
    actual, _ = sf.read(output, dtype="float32", always_2d=True)
    a, b = metrics["start_frame"], metrics["end_frame"]
    assert np.array_equal(actual[:a], source[:a])
    assert np.array_equal(actual[b:], source[b:])
    assert np.array_equal(actual[rate : rate + 100], generated[rate : rate + 100])
    assert metrics["changed_region_rms"] > 0.05
    assert np.array_equal(actual[a], source[a])
    assert np.array_equal(actual[b - 1], source[b - 1])


def test_curve_survives_pack_history_and_is_applied_in_actual_wav_render(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        state = client.post("/api/workstation/projects", json={"demo": True}).json()
        prefix = "/api/workstation/projects/" + state["id"]
        for track in state["content"]["tracks"][1:]:
            track["mute"] = True
        state = client.put(
            prefix, json={"revision": state["revision"], "content": state["content"]}
        ).json()

        def export(s):
            response = client.post(prefix + "/export/wav", json={"revision": s["revision"]})
            assert response.status_code == 200, response.text
            return sf.read(
                io.BytesIO(client.get(response.json()["url"]).content),
                dtype="float32",
                always_2d=True,
            )[0]

        baseline = export(state)
        clip = state["content"]["tracks"][0]["clips"][0]
        clip["volume_points"] = [
            {"time": 0, "db": -12},
            {"time": 8, "db": 0},
            {"time": 16, "db": -6},
        ]
        state = client.put(
            prefix, json={"revision": state["revision"], "content": state["content"]}
        ).json()
        rendered = export(state)
        expected = envelope(np.arange(len(baseline)) / 44100, Clip.model_validate(clip))[:, None]
        assert np.max(np.abs(rendered - baseline * expected)) < 3e-7
        packed = client.post(prefix + "/pack", json={"revision": state["revision"]}).json()
        restored = client.post(
            "/api/workstation/projects/import-pack",
            files={"file": ("curve.mwb", client.get(packed["url"]).content)},
        ).json()
        assert restored["content"] == state["content"]
        undo = client.post(prefix + "/history/undo", json={"revision": state["revision"]}).json()
        assert not undo["content"]["tracks"][0]["clips"][0]["volume_points"]
