"""Original score, not a model output. External MIDI assistance, imported through UI.

During the walkthrough the eight-note intro was entered in the GUI.
--include-intro makes a complete standalone score. This script is external
composition assistance, not a built-in Workbench composer.
"""

import argparse
import json
import random
from pathlib import Path

import mido

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=Path("outputs/creations/reproduced-last-tram"))
parser.add_argument("--include-intro", action="store_true")
args = parser.parse_args()
OUT = args.output.resolve()
OUT.mkdir(exist_ok=True, parents=True)
rng = random.Random(20261016)
BPM = 96
TPB = 480
parts = {
    k: []
    for k in [
        "Piano - walking lights",
        "Piano - theme",
        "Bass - footsteps",
        "Marimba - reflections",
        "Pad - first light",
        "Drums - quiet motion",
    ]
}

CHORDS = {
    "Dm9": ([50, 57, 60, 64, 65], 38),
    "Bbmaj7": ([46, 53, 57, 62, 65], 34),
    "Fmaj7": ([48, 53, 57, 60, 64], 41),
    "Cadd9": ([48, 55, 60, 62, 64], 36),
    "F6add9": ([48, 53, 57, 62, 67], 41),
}
harmony = ["Dm9", "Bbmaj7", "Fmaj7", "Cadd9"]
harmony += ["Dm9"] * 2 + ["Bbmaj7"] * 2 + ["Fmaj7"] * 2 + ["Cadd9"] * 2
harmony += ["Bbmaj7", "Cadd9", "Dm9", "Dm9", "Fmaj7", "Cadd9", "Bbmaj7", "Cadd9"]
harmony += ["Dm9", "Bbmaj7", "Fmaj7", "Cadd9", "Dm9", "Bbmaj7", "Cadd9", "Fmaj7"]
harmony += ["Bbmaj7", "Cadd9", "F6add9", "F6add9"]
assert len(harmony) == 32


def note(part, beat, pitch, length, velocity, jitter=0):
    start = max(0, beat + rng.uniform(0, jitter))
    end = min(128, start + length)
    parts[part].append(
        dict(
            start=round(start, 4),
            pitch=pitch,
            length=round(end - start, 4),
            velocity=max(1, min(127, velocity)),
        )
    )


for bar, ch in enumerate(harmony):
    chord, root = CHORDS[ch]
    base = bar * 4
    intro = bar < 4
    outro = bar >= 28
    if bar >= 30:
        if bar == 30:
            for i, p in enumerate([53, 57, 60, 62, 67]):
                note("Piano - walking lights", base + i * 0.04, p, 7.4 - i * 0.04, 58 - i, 0)
        continue
    # Restrained low voicing, then broken upper chord tones.
    note("Piano - walking lights", base, chord[0], 2.7, 50 if intro or outro else 59, 0.025)
    sequence = [(0.5, 2), (2.5, 4)] if intro else [(0.5, 2), (1.5, 3), (2.5, 4), (3.25, 2)]
    if 12 <= bar < 28:
        sequence += [(1, 1), (3.75, 3)]
    for off, index in sequence:
        note(
            "Piano - walking lights",
            base + off,
            chord[index],
            0.68,
            49 + rng.randrange(-5, 7),
            0.025,
        )
    if 4 <= bar < 30:
        note("Bass - footsteps", base, root, 1.65, 76 if bar < 12 else 84, 0.012)
        note("Bass - footsteps", base + 2.5, root + 12, 0.9, 61, 0.015)
        if 12 <= bar < 28:
            note("Bass - footsteps", base + 3.5, root + 7, 0.36, 56, 0.01)
    if bar >= 8 and bar < 28:
        for p in chord[1:4]:
            note("Pad - first light", base + 0.06, p + 12, 3.85, 33 if bar < 20 else 39)
    if bar >= 4 and bar < 30:
        # Original programmed rhythm; no stock GMD pattern used.
        for off in [0, 2.5] if bar < 12 else [0, 1.75, 2.5]:
            note("Drums - quiet motion", base + off, 36, 0.14, 58 + rng.randrange(-5, 6), 0.01)
        for off in [1, 3]:
            note("Drums - quiet motion", base + off, 38, 0.13, 36 + rng.randrange(-5, 6), 0.018)
        for idx in range(8):
            if outro and idx % 2:
                continue
            note(
                "Drums - quiet motion",
                base + idx * 0.5 + (0.025 if idx % 2 else 0),
                42,
                0.08,
                27 + (5 if idx % 2 == 0 else 0) + rng.randrange(-4, 5),
                0.012,
            )
        if bar in [11, 19, 27]:
            for off, vel in [(3.25, 27), (3.5, 35), (3.75, 42)]:
                note("Drums - quiet motion", base + off, 38, 0.1, vel)

# Melody: hand-authored phrases. (offset, pitch, duration); rests are deliberate.
A = [
    (0, 74, 1),
    (1.5, 77, 0.7),
    (2.5, 81, 0.8),
    (3.5, 79, 0.7),
    (5, 76, 1.5),
    (7, 77, 1.5),
    (10, 74, 1.5),
    (12, 72, 0.7),
    (13, 69, 1.6),
    (15, 72, 0.7),
    (16, 77, 1.5),
    (18, 79, 0.7),
    (19, 81, 1.5),
    (21, 79, 0.7),
    (22, 76, 1.4),
    (24, 74, 1.5),
    (26, 72, 0.8),
    (27, 76, 0.8),
    (29, 74, 2.3),
]
B = [
    (0, 77, 1.4),
    (2, 81, 1.2),
    (3.5, 84, 0.7),
    (5, 83, 0.7),
    (6, 79, 1.6),
    (8, 81, 1.4),
    (10, 77, 0.8),
    (11, 76, 0.7),
    (12.5, 74, 2),
    (15, 77, 0.7),
    (16, 81, 1),
    (17.5, 84, 1.3),
    (19, 86, 1.6),
    (21, 84, 0.7),
    (22, 79, 1.5),
    (24, 77, 1.4),
    (26, 79, 0.8),
    (27.5, 76, 1),
    (29, 72, 2.4),
]
Aprime = [
    (0, 74, 0.8),
    (1.25, 77, 0.6),
    (2.25, 81, 0.8),
    (3.5, 79, 0.6),
    (5, 77, 1.2),
    (6.5, 74, 1),
    (8, 77, 1.2),
    (10, 79, 0.8),
    (11, 81, 1.5),
    (13, 79, 0.8),
    (14, 76, 1),
    (16, 74, 1),
    (17.5, 77, 0.6),
    (18.5, 81, 1),
    (20, 79, 1.5),
    (22, 77, 1.4),
    (24, 76, 1),
    (25.5, 79, 0.7),
    (27, 77, 1.7),
    (30, 72, 1.5),
]
for begin, phrase, vel in [(16, A, 79), (48, B, 84), (80, Aprime, 82)]:
    for off, p, length in phrase:
        note("Piano - theme", begin + off, p, length, vel + rng.randrange(-7, 5), 0.012)
for off, p, length in [(0, 74, 1.5), (3, 77, 1.4), (5, 76, 1.5), (8, 77, 6.8)]:
    note("Piano - theme", 112 + off, p, length, 60 + rng.randrange(-4, 4), 0.01)
for bar in [12, 14, 16, 18, 20, 22, 24, 26]:
    chord, _ = CHORDS[harmony[bar]]
    for off, index in [(1.5, 2), (2.75, 3), (3.5, 4)]:
        note(
            "Marimba - reflections",
            bar * 4 + off,
            chord[index] + 12,
            0.48,
            43 + rng.randrange(-4, 6),
            0.015,
        )
note("Bass - footsteps", 120, 41, 6.8, 58)
for p in [57, 62, 65, 67]:
    note("Pad - first light", 120.05, p, 7.8, 27)

manual_intro = [
    [0, 74, 1, 72],
    [1.5, 77, 0.75, 76],
    [2.5, 81, 0.75, 82],
    [3.5, 79, 1, 73],
    [5, 76, 1.5, 65],
    [7, 77, 1.5, 70],
    [10, 74, 1.75, 63],
    [13, 69, 2.5, 58],
]
if args.include_intro:
    parts["Piano - motif intro"] = [
        dict(start=b, pitch=p, length=length, velocity=v) for b, p, length, v in manual_intro
    ]
mid = mido.MidiFile(type=1, ticks_per_beat=TPB, charset="utf-8")
meta = mido.MidiTrack()
mid.tracks.append(meta)
meta.append(mido.MetaMessage("track_name", name="After the Last Tram - original composition"))
meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM)))
meta.append(mido.MetaMessage("time_signature", numerator=4, denominator=4))
previous_marker = 0
for bar, label in [
    (0, "Intro"),
    (4, "A - Walking alone"),
    (12, "B - Windows light up"),
    (20, "A2 - Toward morning"),
    (28, "Outro"),
]:
    tick = bar * 4 * TPB
    meta.append(mido.MetaMessage("marker", text=label, time=tick - previous_marker))
    previous_marker = tick
programs = [0, 0, 33, 12, 89, 0] + ([0] if args.include_intro else [])
channels = [0, 1, 2, 3, 4, 9] + ([5] if args.include_intro else [])
for (name, notes), program, channel in zip(parts.items(), programs, channels, strict=True):
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("track_name", name=name))
    track.append(mido.Message("program_change", channel=channel, program=program))
    events = []
    for n in notes:
        start = round(n["start"] * TPB)
        end = round((n["start"] + n["length"]) * TPB)
        events.extend(
            [
                (
                    start,
                    1,
                    mido.Message(
                        "note_on", channel=channel, note=n["pitch"], velocity=n["velocity"]
                    ),
                ),
                (end, 0, mido.Message("note_off", channel=channel, note=n["pitch"], velocity=0)),
            ]
        )
    previous = 0
    for tick, _, event in sorted(events, key=lambda e: (e[0], e[1])):
        event.time = tick - previous
        track.append(event)
        previous = tick
    track.append(mido.MetaMessage("end_of_track", time=max(0, 128 * TPB - previous)))
midi_path = OUT / (
    "after-the-last-tram.mid" if args.include_intro else "arrangement-assistance.mid"
)
mid.save(midi_path)
score = {
    "title": "末班车后的微光 / After the Last Tram",
    "bpm": BPM,
    "time_signature": "4/4",
    "duration_seconds": 80,
    "seed_for_microtiming": 20261016,
    "harmony_by_bar": harmony,
    "sections": [
        {"bar": 1, "name": "Intro", "seconds": 0},
        {"bar": 5, "name": "A", "seconds": 10},
        {"bar": 13, "name": "B", "seconds": 30},
        {"bar": 21, "name": "A2", "seconds": 50},
        {"bar": 29, "name": "Outro", "seconds": 70},
    ],
    "parts": parts,
    "manual_intro": manual_intro,
}
(OUT / "score.json").write_text(json.dumps(score, ensure_ascii=False, indent=2), encoding="utf-8")
print(
    json.dumps(
        {"midi": str(midi_path), "notes": {k: len(v) for k, v in parts.items()}}, ensure_ascii=False
    )
)
