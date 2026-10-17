import sys
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf

from music_studio.studio import polyphony


def test_bad_checkpoint_fails_before_loading_optional_runtime(tmp_path):
    source = tmp_path / "input.wav"
    sf.write(source, np.zeros(4410), 44100)
    with pytest.raises(ValueError, match="Prepare or repair"):
        polyphony.extract(source, tmp_path, {"model_dir": str(tmp_path)})
    checkpoint = tmp_path / polyphony.MODEL_PATH
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"damaged")
    with pytest.raises(ValueError, match="Prepare or repair"):
        polyphony.extract(source, tmp_path, {"model_dir": str(tmp_path)})


def test_upstream_contract_keeps_polyphony_thresholds_clamps_bounds_and_velocity(
    tmp_path, monkeypatch
):
    source = tmp_path / "input.wav"
    sf.write(source, np.zeros(44100), 44100)
    checkpoint = tmp_path / polyphony.MODEL_PATH
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"test")
    monkeypatch.setattr(polyphony, "sha256", lambda _: polyphony.MODEL_SHA)
    calls = []

    def predict(path, model, **options):
        calls.append(options)
        midi = SimpleNamespace(write=lambda path: None)
        return (
            {},
            midi,
            [
                (-0.01, 0.7, 60, 0.5),
                (0, 1.2, 64, 0.8),
                (0.2, 0.1, 67, 0.7),
                (0.4, 0.9, 69, float("nan")),
            ],
        )

    monkeypatch.setitem(
        sys.modules, "basic_pitch.inference", SimpleNamespace(Model=lambda _: None, predict=predict)
    )
    before = sys.path.copy()
    try:
        result = polyphony.extract(
            source,
            tmp_path,
            dict(model_dir=str(tmp_path), note_onset=0.6, note_frame=0.35, note_min_ms=140),
        )
    finally:
        sys.path[:] = before
    assert [(n.start, n.end, n.pitch, n.velocity) for n in result.notes] == [
        (0, 0.7, 60, 64),
        (0, 1, 64, 102),
    ]
    assert calls == [
        dict(
            onset_threshold=0.6,
            frame_threshold=0.35,
            minimum_note_length=140,
            multiple_pitch_bends=False,
        )
    ]
    assert result.notes[0].end > result.notes[1].start  # Chords are not collapsed to one pitch.
