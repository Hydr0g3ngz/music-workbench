"""Map task-relative output seconds back to the selected source clip."""

import struct


def stable_wav_header(path):
    """libsndfile's optional PEAK timestamp must not randomize a pinned input hash."""
    with path.open("r+b") as file:
        if file.read(4) != b"RIFF":
            raise ValueError("Expected a canonical RIFF WAV snapshot")
        file.seek(12)
        while header := file.read(8):
            kind, size = struct.unpack("<4sI", header)
            position = file.tell()
            if kind == b"PEAK" and size >= 8:
                # Preserve PEAK version/values and all waveform samples.
                file.seek(position + 4)
                file.write(b"\0" * 4)
            file.seek(position + size + size % 2)


def source_origin(task):
    # Tasks saved before ranged processing used the complete source.
    return (task.get("source_range") or {}).get("start", 0)


def clip_window(task):
    clip = task["source_clip"]
    ratio = task.get("time_ratio", 1) if task["stage"] == "transform" else 1
    if (task.get("source_range") or {}).get("scope") == "clip":
        audio = task["input_audio"]
        return 0, round(audio["frames"] / ratio) / audio["sample_rate"]
    return max(0, clip["offset"] - source_origin(task)) / ratio, clip["duration"] / ratio
