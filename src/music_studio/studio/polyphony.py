"""Pinned Spotify Basic Pitch ONNX runtime, isolated from TensorFlow and Torch."""

import sys
from pathlib import Path

from ..io import sha256

WHEEL_URL = (
    "https://files.pythonhosted.org/packages/99/0e/"
    "3a36d22562daeb0ae3c78ac78da3f8dba96543c5576ed57d4acb8ddbab5b/"
    "basic_pitch-0.4.0-py2.py3-none-any.whl"
)
WHEEL_SHA = "738adb503aae7fdfc7d1e1511aa0ce35052315f260a19531ef4c356708425db0"
MODEL_SHA = "2c3c1d144bfa61ad236e92e169c13535c880469a12a047d4e73451f2c059a0ec"
MODEL_PATH = "basic-pitch-source/basic_pitch/saved_models/icassp_2022/nmp.onnx"


def install_assets(root, cache):
    import zipfile

    from .ai_install_worker import download

    archive = cache / "basic_pitch-0.4.0.whl"
    download(WHEEL_URL, archive, WHEEL_SHA)
    folder = (root / "models/basic-pitch-source").resolve()
    files = []
    with zipfile.ZipFile(archive) as package:
        for item in package.infolist():
            if not (
                item.filename.startswith("basic_pitch/")
                and (item.filename.endswith(".py") or item.filename.endswith("nmp.onnx"))
            ):
                continue
            path = (folder / item.filename).resolve()
            if not path.is_relative_to(folder):
                raise ValueError("Invalid Basic Pitch source path")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(package.read(item))
            files.append(path)
        license_path = folder / "LICENSE"
        license_path.write_bytes(package.read("basic_pitch-0.4.0.dist-info/LICENSE"))
        files.append(license_path)
    if sha256(root / "models" / MODEL_PATH) != MODEL_SHA:
        raise ValueError("Basic Pitch ONNX checkpoint mismatch")
    return files


def extract(source, output, config):
    import math

    import soundfile as sf

    from ..schema import Melody, Note

    model = Path(config["model_dir"]) / MODEL_PATH
    if not model.is_file() or sha256(model) != MODEL_SHA:
        raise ValueError("Prepare or repair the Polyphonic notes pack before transcription")
    sys.path.insert(0, str(model.parents[3]))
    # Source comes from the hash-verified upstream wheel. Its ONNX dependencies are
    # installed separately; the TensorFlow distribution and metadata are not installed.
    from basic_pitch.inference import Model, predict

    network = Model(model)
    _, midi, events = predict(
        source,
        network,
        onset_threshold=config.get("note_onset", 0.5),
        frame_threshold=config.get("note_frame", 0.3),
        minimum_note_length=config.get("note_min_ms", 127.7),
        multiple_pitch_bends=False,
    )
    duration = sf.info(source).duration
    notes = []
    for start, end, pitch, amplitude, *_ in sorted(events, key=lambda e: (e[0], e[2])):
        if not all(math.isfinite(v) for v in (start, end, pitch, amplitude)):
            continue
        start, end = max(0, float(start)), min(duration, float(end))
        if end <= start or not 0 <= pitch <= 127:
            continue
        notes.append(
            Note(
                id=f"n{len(notes)}",
                start=start,
                end=end,
                pitch=int(pitch),
                velocity=max(1, min(127, round(float(amplitude) * 127))),
                score=max(0, min(1, float(amplitude))),
            )
        )
    midi.write(str(output / "melody.mid"))
    return Melody(
        backend="spotify-basic-pitch-0.4.0-onnx-cpu",
        notes=notes,
        pitch_file="",
        warnings=[
            "Polyphonic estimates for one instrument; inspect chords, timing and velocity. "
            "Pitch bends are not imported into the piano roll."
        ],
    )
