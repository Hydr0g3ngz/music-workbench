import hashlib
import io

import mido
import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from music_studio.studio import library, midi_import
from music_studio.studio.service import StudioError
from music_studio.ui.server import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as app:
        yield app


def project(client):
    return client.post("/api/workstation/projects", json={"title": "Creation test"}).json()


def midi_bytes(tracks, kind=1):
    midi = mido.MidiFile(type=kind, ticks_per_beat=480)
    midi.tracks.extend(mido.MidiTrack(track) for track in tracks)
    result = io.BytesIO()
    midi.save(file=result)
    return result.getvalue()


def test_pack_is_offline_small_and_has_verifiable_sources(client):
    response = client.get("/api/workstation/library")
    assert response.status_code == 200
    data = response.json()
    assert len(data["samples"]) == 23 and len(data["patterns"]) == 8
    assert data["origin"]["license"] == "CC0-1.0"
    assert sum(library.sample_path(s["id"]).stat().st_size for s in data["samples"]) < 4_000_000
    for sample in data["samples"]:
        response = client.get(sample["url"])
        assert response.status_code == 200
        assert hashlib.sha256(response.content).hexdigest() == sample["sha256"]
        audio, rate = sf.read(io.BytesIO(response.content), always_2d=True)
        assert rate == 44100 and audio.shape == (sample["frames"], 2)
        assert np.isfinite(audio).all() and 0 < abs(audio).max() < 1
        assert sample["source_sha256"] and data["vcsl_revision"] in sample["source_url"]
    assert client.get("/api/workstation/library/samples/unknown").status_code == 404


def test_real_groove_is_editable_credited_and_reversible(client):
    state = project(client)
    prefix = f"/api/workstation/projects/{state['id']}"
    result = client.post(
        prefix + "/patterns",
        json={
            "revision": state["revision"],
            "pattern": "groove-funk",
            "at": 1,
        },
    )
    assert result.status_code == 200, result.text
    state = result.json()
    track = state["content"]["tracks"][0]
    clip = track["clips"][0]
    assert track["instrument"] == "vcsl-drums" and len(clip["notes"]) > 15
    assert clip["duration"] == pytest.approx(8 * 60 / 108)
    assert clip["origin"]["license"] == "CC-BY-4.0"
    credits = client.get(prefix + "/credits").text
    assert "Jon Gillick" in credits and "Versilian" in credits and "CC-BY-4.0" in credits
    assert (
        client.post(
            prefix + "/patterns",
            json={
                "revision": 0,
                "pattern": "groove-rock",
            },
        ).status_code
        == 409
    )
    assert (
        client.post(
            prefix + "/patterns",
            json={
                "revision": state["revision"],
                "pattern": "groove-rock",
                "use_source_tempo": True,
            },
        ).status_code
        == 422
    )
    exported = client.post(prefix + "/export/mid", json={"revision": state["revision"]}).json()
    midi = mido.MidiFile(file=io.BytesIO(client.get(exported["url"]).content))
    assert {m.channel for t in midi.tracks for m in t if m.type == "note_on"} == {9}
    reverted = client.post(prefix + "/history/undo", json={"revision": state["revision"]}).json()
    assert reverted["content"]["tracks"] == []
    restored = client.post(prefix + "/history/redo", json={"revision": reverted["revision"]}).json()
    assert restored["content"] == state["content"]


def test_sampled_piano_wav_contains_expected_transposed_pitch(client):
    raw = midi_bytes(
        [
            [
                mido.Message("note_on", note=69, velocity=100),
                mido.Message("note_off", note=69, time=960),
            ]
        ]
    )
    state = project(client)
    prefix = f"/api/workstation/projects/{state['id']}"
    result = client.post(prefix + "/midi?revision=0", files={"file": ("A4.mid", raw)})
    assert result.status_code == 200, result.text
    state = result.json()
    assert state["content"]["tracks"][0]["instrument"] == "vcsl-piano"
    exported = client.post(prefix + "/export/wav", json={"revision": state["revision"]}).json()
    audio, rate = sf.read(io.BytesIO(client.get(exported["url"]).content), always_2d=True)
    signal = audio[round(0.08 * rate) : round(0.7 * rate)].mean(axis=1)
    frequency = np.fft.rfftfreq(len(signal), 1 / rate)
    power = np.abs(np.fft.rfft(signal * np.hanning(len(signal))))
    assert power[(frequency > 435) & (frequency < 445)].max() > power.max() * 0.12
    assert 0.01 < np.max(abs(audio)) < 0.5
    # Original bytes remain stored, not silently normalized as MIDI.
    original = library.Path(client.app.state.studio.root) / ".midi-originals"
    assert next(original.glob("*.mid")).read_bytes() == raw


def test_unicode_track_names_survive_midi_export_and_reimport(client):
    state = project(client)
    prefix = f"/api/workstation/projects/{state['id']}"
    raw = midi_bytes(
        [
            [
                mido.Message("note_on", note=74, velocity=82),
                mido.Message("note_off", note=74, time=720),
            ]
        ]
    )
    state = client.post(prefix + "/midi?revision=0", files={"file": ("theme.mid", raw)}).json()
    name = "归途 · 主旋律 / Lead 🎹"
    state["content"]["tracks"][0]["name"] = name
    state = client.put(
        prefix, json={"revision": state["revision"], "content": state["content"]}
    ).json()
    response = client.post(prefix + "/export/mid", json={"revision": state["revision"]})
    assert response.status_code == 200, response.text
    data = client.get(response.json()["url"]).content
    exported = mido.MidiFile(file=io.BytesIO(data), charset="utf-8")
    assert [m.name for t in exported.tracks for m in t if m.type == "track_name"] == [name]
    assert sum(m.type == "note_on" for t in exported.tracks for m in t) == 1
    fresh = project(client)
    imported = client.post(
        f"/api/workstation/projects/{fresh['id']}/midi?revision=0",
        files={"file": ("roundtrip.mid", data)},
    )
    assert imported.status_code == 200, imported.text
    track = imported.json()["content"]["tracks"][0]
    assert track["name"] == name
    assert track["clips"][0]["notes"][0]["velocity"] == 82


def test_legacy_latin1_midi_names_still_import(client):
    raw = midi_bytes(
        [
            [
                mido.MetaMessage("track_name", name="Café"),
                mido.Message("note_on", note=60, velocity=70),
                mido.Message("note_off", note=60, time=480),
            ]
        ]
    )
    state = project(client)
    result = client.post(
        f"/api/workstation/projects/{state['id']}/midi?revision=0",
        files={"file": ("legacy.mid", raw)},
    )
    assert result.status_code == 200, result.text
    assert result.json()["content"]["tracks"][0]["name"] == "Café"


def test_failed_midi_write_does_not_leave_partial_download(client, tmp_path, monkeypatch):
    state = project(client)
    prefix = f"/api/workstation/projects/{state['id']}"
    raw = midi_bytes(
        [[mido.Message("note_on", note=60), mido.Message("note_off", note=60, time=480)]]
    )
    state = client.post(prefix + "/midi?revision=0", files={"file": ("theme.mid", raw)}).json()

    def failed_save(_midi, filename=None, **_kwargs):
        library.Path(filename).write_bytes(b"MThd")
        raise ValueError("Interrupted MIDI encoding")

    monkeypatch.setattr(mido.MidiFile, "save", failed_save)
    response = client.post(prefix + "/export/mid", json={"revision": state["revision"]})
    assert response.status_code == 422
    assert not list((tmp_path / ".arrangement-exports").glob("*.mid"))
    assert client.get(prefix).json()["content"] == state["content"]


def test_tempo_changes_sustain_and_channels_preserve_performance_time(client):
    raw = midi_bytes(
        [
            [
                mido.MetaMessage("set_tempo", tempo=500000),
                mido.MetaMessage("set_tempo", tempo=1000000, time=480),
            ],
            [
                mido.Message("program_change", channel=0, program=12),
                mido.Message("control_change", channel=0, control=64, value=127),
                mido.Message("note_on", channel=0, note=60, velocity=87),
                mido.Message("note_off", channel=0, note=60, time=480),
                mido.Message("control_change", channel=0, control=64, value=0, time=480),
                mido.Message("note_on", channel=0, note=72, velocity=74),
                mido.Message("note_off", channel=0, note=72, time=480),
            ],
            [
                mido.Message("note_on", channel=9, note=36, velocity=100, time=480),
                mido.Message("note_off", channel=9, note=36, time=120),
            ],
        ]
    )
    info = client.post("/api/workstation/midi/inspect", files={"file": ("tempo.mid", raw)}).json()
    assert info["track_count"] == 2 and "tempo_map" in info["warnings"]
    assert info["duration"] == pytest.approx(2.5)
    state = project(client)
    prefix = f"/api/workstation/projects/{state['id']}"
    result = client.post(prefix + "/midi?revision=0&at=2", files={"file": ("tempo.mid", raw)})
    assert result.status_code == 200, result.text
    state = result.json()
    marimba = next(t for t in state["content"]["tracks"] if t["instrument"] == "vcsl-marimba")
    notes = marimba["clips"][0]["notes"]
    assert notes[0]["length"] * 60 / 108 == pytest.approx(1.5)
    assert notes[1]["start"] * 60 / 108 == pytest.approx(1.5)
    assert [n["velocity"] for n in notes] == [87, 74]
    assert marimba["clips"][0]["start"] == 2
    assert (
        client.post(prefix + "/midi?revision=0", files={"file": ("tempo.mid", raw)}).status_code
        == 409
    )


def test_dense_midi_splits_without_losing_notes():
    track = []
    for _ in range(1025):
        track.extend(
            [
                mido.Message("note_on", note=60, velocity=80),
                mido.Message("note_off", note=60, time=1),
            ]
        )
    parsed = midi_import.inspect_midi(midi_bytes([track]))
    parts = midi_import.parts(parsed, 120)
    assert len(parts) == 1 and len(parts[0]["clips"]) == 3
    assert sum(len(c["notes"]) for c in parts[0]["clips"]) == 1025


@pytest.mark.parametrize(
    "raw",
    [
        b"not MIDI",
        b"MThd\x00",
        midi_bytes(
            [
                [
                    mido.Message("note_on", note=60, velocity=80),
                    mido.Message("note_off", note=60, time=480),
                ]
            ],
            kind=2,
        ),
    ],
)
def test_invalid_midi_is_actionable_422(client, raw):
    response = client.post("/api/workstation/midi/inspect", files={"file": ("broken.mid", raw)})
    assert response.status_code == 422 and response.json()["detail"]


def test_import_limits_and_tempo_adoption(client):
    with pytest.raises(StudioError, match="8 MiB"):
        midi_import.inspect_midi(b"0" * (8 * 1024 * 1024 + 1))
    raw = midi_bytes(
        [
            [
                mido.MetaMessage("set_tempo", tempo=750000),
                mido.Message("note_on", note=0, velocity=50),
                mido.Message("note_off", note=0, time=480),
            ]
        ]
    )
    state = project(client)
    prefix = f"/api/workstation/projects/{state['id']}"
    response = client.post(
        prefix + "/midi?revision=0&use_source_tempo=true", files={"file": ("low.mid", raw)}
    )
    assert response.status_code == 200, response.text
    assert response.json()["content"]["bpm"] == 80
    assert response.json()["content"]["tracks"][0]["clips"][0]["notes"][0]["pitch"] == 0
