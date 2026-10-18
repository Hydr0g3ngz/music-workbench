"""Pinned Transkun inference source, without training-only native dependencies."""

import json
import math
import sys
from pathlib import Path

from ..io import sha256

WHEEL_URL = "https://files.pythonhosted.org/packages/a2/1f/1e04ac0f04583d593ecca935270401404ad45e88c9db7b249b67bde20a1b/transkun-2.0.1-py3-none-any.whl"
WHEEL_SHA = "7d7f5bf88b0d21f7da0415b089cff3bcbcbdda04e1a3c9719964947942c859fe"
MODEL_SHA = "50a80010effc2a59ffcd068a95cd2b29bd7f23a27a3515bc3ccd209c89a3d44c"
CONFIG_SHA = "d3d989214eb148230ee5df476d994dcde6af595904d3f968f1221d2e3bea5ac6"
MODEL_PATH = "transkun-source/transkun/pretrained/2.0.pt"


def install_assets(root, cache):
    import zipfile

    from .ai_install_worker import download

    archive = cache / "transkun-2.0.1-py3-none-any.whl"
    download(WHEEL_URL, archive, WHEEL_SHA)
    folder = (root / "models/transkun-source").resolve()
    files = []
    with zipfile.ZipFile(archive) as package:
        for item in package.infolist():
            if not item.filename.startswith("transkun/") or not item.filename.endswith(
                (".py", "2.0.pt", "2.0.conf")
            ):
                continue
            path = (folder / item.filename).resolve()
            if not path.is_relative_to(folder):
                raise ValueError("Invalid Transkun package path")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(package.read(item))
            files.append(path)
        license_file = folder / "LICENSE"
        license_file.write_bytes(package.read("transkun-2.0.1.dist-info/LICENSE"))
        files.append(license_file)
    for path, expected in [
        (root / "models" / MODEL_PATH, MODEL_SHA),
        ((root / "models" / MODEL_PATH).with_suffix(".conf"), CONFIG_SHA),
    ]:
        if sha256(path) != expected:
            raise ValueError("Transkun checkpoint/configuration mismatch")
    return files


def extract(source, output, config):
    import numpy as np
    import soundfile as sf

    from ..schema import Melody, Note

    model_path = Path(config["model_dir"]) / MODEL_PATH
    conf_path = model_path.with_suffix(".conf")
    if (
        not model_path.is_file()
        or sha256(model_path) != MODEL_SHA
        or not conf_path.is_file()
        or sha256(conf_path) != CONFIG_SHA
    ):
        raise ValueError("Prepare or repair the Piano notes pack before transcription")
    import torch

    sys.path.insert(0, str(model_path.parents[2]))
    from transkun.ModelTransformer import ModelConfig, TransKun

    options = ModelConfig()
    for key, value in json.loads(conf_path.read_text())["Model"]["config"].items():
        setattr(options, key, value)
    device = config.get("device", "cpu")
    model = TransKun(conf=options).to(device)
    # Only the hash-pinned official checkpoint is deserialized, never a user model file.
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    model.load_state_dict(
        checkpoint.get("best_state_dict", checkpoint.get("state_dict")), strict=True
    )
    model.eval()
    audio, rate = sf.read(source, dtype="float32", always_2d=True)
    if rate != model.fs:
        from scipy.signal import resample_poly

        divisor = math.gcd(rate, model.fs)
        audio = resample_poly(audio, model.fs // divisor, rate // divisor, axis=0).astype(
            np.float32
        )
    duration = sf.info(source).duration
    with torch.inference_mode():
        events = model.transcribe(
            torch.from_numpy(audio).to(device),
            stepInSecond=8,
            segmentSizeInSecond=16,
            discardSecondHalf=False,
        )
    notes = []
    for event in sorted(events, key=lambda n: (n.start, n.pitch)):
        if not all(math.isfinite(v) for v in (event.start, event.end, event.pitch, event.velocity)):
            continue
        start, end = max(0, float(event.start)), min(duration, float(event.end))
        if end <= start or not 0 <= event.pitch <= 127:
            continue
        notes.append(
            Note(
                id=f"n{len(notes)}",
                start=start,
                end=end,
                pitch=int(event.pitch),
                velocity=max(1, min(127, round(event.velocity))),
                score=0,
            )
        )
    return Melody(
        backend="transkun-2.0.1-fp32",
        notes=notes,
        pitch_file="",
        warnings=[
            "Piano-only note estimates. Check note timing and velocity. Pedal/control events "
            "are not imported into the piano roll; checkpoint uses key-release note offsets. "
            "No calibrated note confidence is exposed; score=0 means unavailable."
        ],
    )
