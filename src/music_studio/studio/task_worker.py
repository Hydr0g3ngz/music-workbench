"""One isolated capability invocation. Exiting releases its model and GPU memory."""

import csv
import os
import sys
import threading
import time
from pathlib import Path

from ..io import read_json, sha256, write_json


def owner_alive(pid):
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def watch_owner(pid):
    while True:
        if not owner_alive(pid):
            os._exit(130)
        time.sleep(1)


def synthesize_notes(path, melody, duration, rate=44100):
    """Neutral, clearly labeled note synthesis. Bounded memory and unquantized time."""
    import numpy as np
    import soundfile as sf

    frames = round(duration * rate)
    with sf.SoundFile(path, "w", samplerate=rate, channels=2, subtype="FLOAT") as output:
        for first in range(0, frames, 65536):
            times = np.arange(first, min(frames, first + 65536)) / rate
            block = np.zeros(len(times), dtype=np.float64)
            for note in melody.notes:
                mask = (times >= note.start) & (times < note.end)
                if not mask.any():
                    continue
                local = times[mask] - note.start
                length = note.end - note.start
                envelope = np.minimum(1, local / 0.005) * np.minimum(1, (length - local) / 0.035)
                phase = local * 2 * np.pi * 440 * 2 ** ((note.pitch - 69) / 12)
                block[mask] += envelope * (0.18 * np.sin(phase) + 0.035 * np.sin(phase * 2))
            output.write(np.column_stack([block, block]).astype(np.float32))


def execute(request):
    source, output = Path(request["input"]), Path(request["output"])
    config = request["settings"]
    if sha256(source) != request["input_sha256"]:
        raise ValueError("Pinned input hash does not match")
    output.mkdir(parents=True, exist_ok=True)
    stage, model = request["stage"], request["model"]
    started = time.perf_counter()
    artifacts = []
    import soundfile as sf

    duration = sf.info(source).duration
    if stage != "inspect":
        import random

        import numpy as np

        random.seed(config["seed"])
        np.random.seed(config["seed"])
    if stage not in ("inspect", "rhythm", "loudness", "denoise", "musical", "transform"):
        import torch

        torch.manual_seed(config["seed"])
        torch.set_num_threads(config["threads"])
        config["device"] = (
            ("cuda" if torch.cuda.is_available() else "cpu")
            if config["device"] == "auto"
            else config["device"]
        )
        if config["device"] == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA is unavailable; choose CPU or Auto")
        if config["device"] == "cuda":
            # Catch unsupported architectures/driver kernels before loading weights.
            torch.ones(1, device="cuda").sum().item()
            torch.cuda.reset_peak_memory_stats()

        def reject_download(*args, **kwargs):
            raise RuntimeError("Model is not cached; no automatic download is allowed")

        torch.hub.download_url_to_file = reject_download
    else:
        config["device"] = "cpu"

    def artifact(role, kind, relative, mime):
        artifacts.append({"role": role, "kind": kind, "file": relative, "mime": mime})

    if stage == "musical":
        from .musical import analyze

        write_json(output / "musical.json", analyze(source))
        artifact("musical-analysis", "json", "musical.json", "application/json")
    elif stage == "transform":
        from .musical import transform

        report = transform(
            source, output / "transformed.wav", config["time_ratio"], config["pitch_shift"]
        )
        write_json(output / "transform.json", report)
        artifact("transformed", "audio", "transformed.wav", "audio/wav")
        artifact("transform-report", "json", "transform.json", "application/json")
    elif stage == "inspect":
        from .dsp import inspect_audio

        write_json(output / "levels.json", inspect_audio(source))
        artifact("levels", "json", "levels.json", "application/json")
    elif stage == "loudness":
        from .loudness import measure

        write_json(output / "loudness.json", measure(source))
        artifact("loudness", "json", "loudness.json", "application/json")
    elif stage == "denoise":
        from .cleanup import enhance

        report = enhance(
            source,
            output / "cleaned.wav",
            config["model_dir"],
            strength=config["cleanup_strength"],
            threads=config["threads"],
            model=model,
        )
        write_json(output / "cleanup.json", report)
        artifact("cleaned-speech", "audio", "cleaned.wav", "audio/wav")
        artifact("cleanup-report", "json", "cleanup.json", "application/json")
    elif stage == "separate":
        if model == "mel-band-roformer-kj":
            from .separation import separate
        else:
            from ..backends.separation import separate

        report = separate(source, output, config)
        write_json(output / "separation.json", report)
        artifact("separation-report", "json", "separation.json", "application/json")
        roles = (
            ("drums", "bass", "vocals", "other")
            if model == "demucs-four-stems"
            else ("vocals", "instrumental")
        )
        for role in roles:
            artifact(role, "audio", f"audio/{role}.wav", "audio/wav")
    elif stage == "lyrics":
        from ..backends.lyrics import transcribe
        from .transcripts import write_text_exports

        config.update(
            asr_backend="qwen" if model == "qwen3-asr" else "whisper", lyrics_alignment="native"
        )
        lyrics = transcribe(source, config)
        write_json(output / "lyrics.json", lyrics.model_dump())
        artifact("lyrics", "transcript", "lyrics.json", "application/json")
        for name in write_text_exports(output, lyrics):
            artifact("lyrics-" + name.split(".")[-1], "text", name, "text/plain; charset=utf-8")
    elif stage == "melody":
        from ..backends.melody import extract_melody
        from ..export import write_midi
        from ..schema import Lyrics, Rhythm

        config["melody_decoder"] = "rest" if model == "crepe-rest" else "stable"
        melody = extract_melody(source, output, config)
        write_json(output / "melody.json", melody.model_dump())
        write_midi(
            output / "melody.mid",
            melody,
            Rhythm(backend="natural-time", bpm=120, beats=[]),
            Lyrics(language=None, timing_method="none", segments=[]),
        )
        synthesize_notes(output / "melody-preview.wav", melody, duration)
        artifact("melody", "json", "melody.json", "application/json")
        artifact("midi", "midi", "melody.mid", "audio/midi")
        artifact("note-synthesis", "audio", "melody-preview.wav", "audio/wav")
        artifact("pitch", "json", "analysis/pitch.json", "application/json")
    elif stage == "rhythm":
        from ..backends.rhythm import estimate_rhythm

        rhythm = estimate_rhythm(source, config)
        write_json(output / "rhythm.json", rhythm.model_dump())
        with (output / "beats.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["time_seconds"])
            writer.writerows([[beat] for beat in rhythm.beats])
        artifact("rhythm", "json", "rhythm.json", "application/json")
        artifact("beats", "text", "beats.csv", "text/csv")
    else:
        raise ValueError("Unknown fixed task stage")
    if sha256(source) != request["input_sha256"]:
        raise ValueError("Pinned input changed while processing")
    peak = None
    if config["device"] == "cuda":
        import torch

        if model != "whisper-small":
            peak = round(torch.cuda.max_memory_allocated() / 1024**2, 2)
    result = {
        "artifacts": artifacts,
        "metrics": {
            "seconds": round(time.perf_counter() - started, 3),
            "audio_seconds": round(duration, 3),
            "realtime_factor": round((time.perf_counter() - started) / max(duration, 0.001), 3),
            "device": config["device"],
            "compute_type": config.get("_compute_type"),
            "torch_peak_mb": peak,
            "memory_note": "Torch allocator only; excludes CUDA context and CTranslate2.",
        },
    }
    write_json(output / "result.json", result)


if __name__ == "__main__":
    request = read_json(Path(sys.argv[1]))
    threading.Thread(target=watch_owner, args=(request["owner_pid"],), daemon=True).start()
    execute(request)
