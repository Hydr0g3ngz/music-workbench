"""Bounded Standard MIDI import with explicit tempo/time-signature handling."""

import io
from collections import defaultdict, deque

import mido

from .service import StudioError


def inspect_midi(raw):
    if len(raw) > 8 * 1024 * 1024:
        raise StudioError("MIDI upload limit is 8 MiB", 413)
    try:
        # MIDI has no text-encoding flag. Prefer Unicode files we export while
        # retaining names in older Latin-1 files without dropping metadata.
        try:
            midi = mido.MidiFile(file=io.BytesIO(raw), clip=False, charset="utf-8")
        except UnicodeDecodeError:
            midi = mido.MidiFile(file=io.BytesIO(raw), clip=False, charset="latin-1")
        if midi.type == 2 or midi.ticks_per_beat <= 0:
            raise StudioError("Independent type-2 sequences and SMPTE MIDI are not supported")
        if len(midi.tracks) > 128:
            raise StudioError("MIDI has too many tracks")
        tempo, tick, seconds = 500000, 0, 0.0
        active, sustained, pedals = defaultdict(deque), defaultdict(list), defaultdict(bool)
        names, programs, notes, tempos, signatures = {}, {}, [], [], []
        # Track identity survives interleaving. Tempo/control messages remain globally ordered.
        events = []
        for index, track in enumerate(midi.tracks):
            at = 0
            for order, event in enumerate(track):
                at += event.time
                events.append((at, index, order, event))
                if len(events) > 200000:
                    raise StudioError("MIDI event limit reached")
        for at, index, _order, event in sorted(events, key=lambda x: x[:3]):
            seconds += mido.tick2second(at - tick, midi.ticks_per_beat, tempo)
            tick = at
            if seconds > 600:
                raise StudioError("This preview supports MIDI up to 10 minutes")
            if event.type == "set_tempo":
                if event.tempo <= 0:
                    raise StudioError("MIDI tempo must be positive")
                tempo = event.tempo
                tempos.append({"seconds": seconds, "bpm": mido.tempo2bpm(tempo)})
            elif event.type == "time_signature":
                signatures.append([event.numerator, event.denominator])
            elif event.type == "track_name":
                names[index] = event.name[:150]
            elif event.type == "program_change":
                programs[(index, event.channel)] = event.program
            elif event.type == "control_change" and event.control == 64:
                pedals[event.channel] = event.value >= 64
                if not pedals[event.channel]:
                    for entry in sustained.pop(event.channel, []):
                        entry["end"] = seconds
                        notes.append(entry)
            elif event.type == "note_on" and event.velocity:
                active[(index, event.channel, event.note)].append(
                    {
                        "track": index,
                        "channel": event.channel,
                        "pitch": event.note,
                        "velocity": event.velocity,
                        "start": seconds,
                        "program": programs.get((index, event.channel), 0),
                    }
                )
            elif event.type == "note_off" or (event.type == "note_on" and not event.velocity):
                queue = active[(index, event.channel, event.note)]
                if queue:
                    entry = queue.popleft()
                    if pedals[event.channel] and event.channel != 9:
                        sustained[event.channel].append(entry)
                    else:
                        entry["end"] = seconds
                        notes.append(entry)
            if len(notes) + sum(map(len, sustained.values())) > 8192:
                raise StudioError("Session supports at most 8192 imported notes")
        dangling = sum(map(len, active.values()))
        for queue in [*active.values(), *sustained.values()]:
            for entry in queue:
                entry["end"] = max(entry["start"] + 0.05, seconds)
                notes.append(entry)
        if not notes or len(notes) > 8192:
            raise StudioError("MIDI must contain 1–8192 notes")
        if len({(n["track"], n["channel"], n["program"]) for n in notes}) > 32:
            raise StudioError("MIDI contains more than 32 instrument parts")
        first_bpm = next((t["bpm"] for t in tempos if t["seconds"] == 0), 120.0)
        if tempos and tempos[0]["seconds"] == 0:
            first_bpm = tempos[0]["bpm"]
        warnings = []
        if len({round(t["bpm"], 6) for t in tempos}) > 1:
            warnings.append("tempo_map")
        if any(signature != [4, 4] for signature in signatures):
            warnings.append("time_signature")
        if any(
            n["channel"] != 9 and n["program"] not in (0, 12, 32, 33, 34, 35, 36, 37, 38, 39)
            for n in notes
        ):
            warnings.append("instrument_mapping")
        if dangling:
            warnings.append("unclosed_notes")
        drum_keys = {
            35,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            55,
            57,
            59,
            22,
            26,
        }
        if any(n["channel"] == 9 and n["pitch"] not in drum_keys for n in notes):
            warnings.append("drum_mapping")
        return {
            "notes": notes,
            "names": names,
            "bpm": round(first_bpm, 6),
            "note_count": len(notes),
            "track_count": len({(n["track"], n["channel"], n["program"]) for n in notes}),
            "duration": max(n["end"] for n in notes),
            "warnings": warnings,
            "tempos": tempos,
            "signatures": signatures,
        }
    except (EOFError, OSError, ValueError, KeyError, IndexError) as error:
        if isinstance(error, StudioError):
            raise
        raise StudioError("Invalid or unsupported MIDI file") from error


def summary(parsed):
    return {key: value for key, value in parsed.items() if key not in ("notes", "names")}


def parts(parsed, bpm, at=0):
    """Convert original wall-clock performance to the project's fixed beat grid."""
    grouped = defaultdict(list)
    for note in parsed["notes"]:
        start = note["start"] * bpm / 60
        grouped[(note["track"], note["channel"], note["program"])].append(
            {
                "pitch": note["pitch"],
                "start": start,
                "length": max(0.001, (note["end"] - note["start"]) * bpm / 60),
                "velocity": note["velocity"],
            }
        )
    result = []
    for (track, channel, program), notes in grouped.items():
        drum = channel == 9
        instrument = (
            "vcsl-drums"
            if drum
            else (
                "vcsl-marimba" if program == 12 else "bass" if 32 <= program <= 39 else "vcsl-piano"
            )
        )
        clips = []
        # Keep dense/long MIDI inside the existing per-clip bounds without dropping notes.
        windows = defaultdict(list)
        for note in sorted(notes, key=lambda n: (n["start"], n["pitch"])):
            windows[int(note["start"] // 32)].append(note)
        for window, entries in windows.items():
            offset = window * 32
            for first in range(0, len(entries), 512):
                selected = [
                    dict(n, start=n["start"] - offset) for n in entries[first : first + 512]
                ]
                length = max(n["start"] + n["length"] for n in selected)
                end = (offset + length) * 60 / bpm + at
                if end > 600:
                    raise StudioError("Imported MIDI would exceed the 10-minute timeline")
                clips.append(
                    {
                        "start": at + offset * 60 / bpm,
                        "duration": max(0.1, length * 60 / bpm),
                        "notes": selected,
                    }
                )
        result.append(
            {
                "name": parsed["names"].get(track) or f"MIDI {track + 1}",
                "instrument": instrument,
                "clips": clips,
            }
        )
    return result
