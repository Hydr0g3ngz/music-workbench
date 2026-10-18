import json
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf

from music_studio.studio import piano_notes


def test_piano_checkpoint_is_verified_before_optional_runtime(tmp_path):
    with pytest.raises(ValueError, match="Prepare or repair"):
        piano_notes.extract(tmp_path / "input.wav", tmp_path, {"model_dir": str(tmp_path)})
    model = tmp_path / piano_notes.MODEL_PATH
    model.parent.mkdir(parents=True)
    model.write_bytes(b"broken")
    model.with_suffix(".conf").write_text("{}")
    with pytest.raises(ValueError, match="Prepare or repair"):
        piano_notes.extract(tmp_path / "input.wav", tmp_path, {"model_dir": str(tmp_path)})


def test_piano_contract_keeps_polyphony_velocity_and_key_release(tmp_path, monkeypatch):
    source = tmp_path / "input.wav"
    sf.write(source, np.zeros((44100, 2)), 44100)
    model = tmp_path / piano_notes.MODEL_PATH
    model.parent.mkdir(parents=True)
    model.write_bytes(b"verified fixture")
    model.with_suffix(".conf").write_text(json.dumps({"Model": {"config": {"fs": 44100}}}))
    monkeypatch.setattr(
        piano_notes,
        "sha256",
        lambda p: piano_notes.CONFIG_SHA if p.suffix == ".conf" else piano_notes.MODEL_SHA,
    )
    calls = []

    class Network:
        def __init__(self, conf):
            self.fs = conf.fs

        def to(self, device):
            return self

        def eval(self):
            pass

        def load_state_dict(self, state, strict):
            assert strict and state == "weights"

        def transcribe(self, audio, **kw):
            calls.append(kw)
            return [
                SimpleNamespace(start=a, end=b, pitch=p, velocity=v)
                for a, b, p, v in [
                    (-0.1, 0.8, 60, 88),
                    (0, 1.2, 64, 140),
                    (0.2, 0.6, 128, 90),
                    (0.4, 0.7, 67, float("nan")),
                    (0.7, 0.6, 72, 60),
                ]
            ]

    monkeypatch.setitem(
        sys.modules,
        "transkun.ModelTransformer",
        SimpleNamespace(ModelConfig=type("Config", (), {}), TransKun=Network),
    )
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(
            load=lambda *a, **kw: {"best_state_dict": "weights"},
            inference_mode=nullcontext,
            from_numpy=lambda a: SimpleNamespace(to=lambda device: a),
        ),
    )
    before = sys.path.copy()
    try:
        result = piano_notes.extract(
            source, tmp_path, {"model_dir": str(tmp_path), "device": "cuda"}
        )
    finally:
        sys.path[:] = before
    assert [(n.start, n.end, n.pitch, n.velocity, n.score) for n in result.notes] == [
        (0, 0.8, 60, 88, 0),
        (0, 1, 64, 127, 0),
    ]
    assert calls == [dict(stepInSecond=8, segmentSizeInSecond=16, discardSecondHalf=False)]
    assert "key-release" in result.warnings[0] and "confidence" in result.warnings[0]
