import io

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from music_studio.studio.effects import Effects, Rack
from music_studio.ui.server import create_app


@pytest.fixture
def setup(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as c:
        state = c.post("/api/workstation/projects", json={"title": "Routing"}).json()
        prefix = "/api/workstation/projects/" + state["id"]
        data = io.BytesIO()
        sf.write(data, np.full((4410, 2), 0.1), 44100, format="WAV", subtype="FLOAT")
        state = c.post(
            prefix + "/import",
            params={"revision": state["revision"]},
            files={"file": ("constant.wav", data.getvalue())},
        ).json()
        state["content"]["master_db"] = 0
        yield c, prefix, state


def save(c, prefix, state):
    r = c.put(prefix, json={"revision": state["revision"], "content": state["content"]})
    assert r.status_code == 200, r.text
    return r.json()


def render(c, prefix, state):
    r = c.post(prefix + "/export/wav", json={"revision": state["revision"]})
    assert r.status_code == 200, r.text
    return sf.read(io.BytesIO(c.get(r.json()["url"]).content), always_2d=True)[0]


def test_post_fader_send_bus_gain_pan_and_solo(setup):
    c, prefix, state = setup
    a, b = "a" * 16, "b" * 16
    state["content"]["buses"] = [
        {"id": a, "name": "Group", "gain_db": -6.020599913},
        {"id": b, "name": "Right return", "pan": 1},
    ]
    state["content"]["tracks"][0].update(
        output=a, gain_db=-6.020599913, sends=[{"bus": b, "gain_db": -6.020599913}]
    )
    state = save(c, prefix, state)
    np.testing.assert_allclose(render(c, prefix, state)[100], [0.025, 0.05], atol=2e-7)
    state["content"]["buses"][1]["solo"] = True
    state = save(c, prefix, state)
    np.testing.assert_allclose(render(c, prefix, state)[100], [0, 0.025], atol=2e-7)
    state["content"]["buses"][1]["mute"] = True
    state = save(c, prefix, state)
    np.testing.assert_allclose(render(c, prefix, state), 0, atol=1e-7)


def test_shared_wet_return_tail_bypass_and_history(setup):
    c, prefix, state = setup
    bus = "b" * 16
    fx = Effects.model_validate({"reverb": {"enabled": True, "mix": 1, "decay": 0.4}})
    state["content"]["buses"] = [{"id": bus, "name": "Wet", "effects": fx.model_dump()}]
    state["content"]["tracks"][0].update(output=bus)
    initial = save(c, prefix, state)
    result = render(c, prefix, initial)
    assert len(result) == 26460  # 100 ms source + 500 ms return tail.
    assert np.max(np.abs(result[:100])) == 0  # A fully wet return has no direct signal.
    assert np.max(np.abs(result[4410:])) > 0.001
    reference = np.zeros_like(result)
    reference[:4410] = 0.1
    np.testing.assert_allclose(result, Rack(fx).process(reference), atol=3e-7)
    initial["content"]["buses"][0]["effects"]["bypass"] = True
    changed = save(c, prefix, initial)
    np.testing.assert_allclose(render(c, prefix, changed), 0.1, atol=2e-7)
    undone = c.post(prefix + "/history/undo", json={"revision": changed["revision"]}).json()
    np.testing.assert_array_equal(render(c, prefix, undone), result)


def test_groups_routes_and_sends_survive_portable_restore(setup):
    c, prefix, state = setup
    state["content"]["tracks"][0]["clips"][0]["group"] = "c" * 16
    state["content"]["buses"] = [{"id": "b" * 16, "name": "Group"}]
    state["content"]["tracks"][0]["output"] = "b" * 16
    state = save(c, prefix, state)
    pack = c.post(prefix + "/pack", json={"revision": state["revision"]}).json()
    restored = c.post(
        "/api/workstation/projects/import-pack",
        files={"file": ("group.mwb", c.get(pack["url"]).content, "application/zip")},
    )
    assert restored.status_code == 201, restored.text
    assert restored.json()["content"] == state["content"]


def test_missing_routes_duplicate_sends_and_feedback_fields_are_rejected(setup):
    c, prefix, state = setup
    track = state["content"]["tracks"][0]
    track["output"] = "f" * 16
    assert (
        c.put(prefix, json={"revision": state["revision"], "content": state["content"]}).status_code
        == 422
    )
    track["output"] = None
    state["content"]["buses"] = [{"id": "b" * 16, "name": "Bus", "output": "b" * 16}]
    assert (
        c.put(prefix, json={"revision": state["revision"], "content": state["content"]}).status_code
        == 422
    )
    state["content"]["buses"][0].pop("output")
    track["sends"] = [{"bus": "b" * 16}, {"bus": "b" * 16}]
    assert (
        c.put(prefix, json={"revision": state["revision"], "content": state["content"]}).status_code
        == 422
    )
