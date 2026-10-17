"""Pinned optional RoFormer runtime; never downloads during inference."""

import inspect
import os
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

from ..audio import write_stem
from ..inference_cache import inference_model
from ..io import read_json, sha256

SOURCE_REVISION = "6fdad13686bb7e84d029ec66f9dbe76e65c93ebf"
MODEL_REVISION = "ac9b0614ab3cd7f77219e18ba494dfd93956c348"
WEIGHT_SHA256 = "87201f4d31afb5bc79993230fc49446918425574db48c01c405e44f365c7559e"


def prepare_attention(attend):
    """Use upstream's legacy SDPA path on Torch without set_priority support."""
    if (
        attend._HAS_SDPA_KERNEL
        and "set_priority" not in inspect.signature(attend.sdpa_kernel).parameters
    ):
        attend._HAS_SDPA_KERNEL = False
    return "priority-sdpa" if attend._HAS_SDPA_KERNEL else "legacy-sdpa"


def runtime(verify=False, config_file=None):
    if config_file is None and "MUSIC_STUDIO_SEPARATION_CONFIG" not in os.environ:
        from .model_setup import managed_runtime

        managed = managed_runtime("mel-band-roformer-kj")
        if managed:
            config_file = managed.get("separation_config")
    path = Path(
        config_file
        or os.environ.get("MUSIC_STUDIO_SEPARATION_CONFIG", ".artifacts/separation-runtime.json")
    )
    if not path.is_file():
        raise ValueError(
            "RoFormer is unavailable. Install or repair Vocals & backing in AI setup, "
            "or check your explicitly configured separation runtime."
        )
    config = read_json(path)
    if (
        config.get("source_revision") != SOURCE_REVISION
        or config.get("model_revision") != MODEL_REVISION
    ):
        raise ValueError("Unsupported separation revision; rerun scripts/setup_separation.py")
    if not Path(config["python"]).is_file():
        raise ValueError("Separation Python is missing")
    root = Path(config["root"])
    for item in config["files"]:
        file = (root / item["file"]).resolve()
        if not file.is_relative_to(root.resolve()) or not file.is_file():
            raise ValueError("Pinned separation file is missing")
        if verify and sha256(file) != item["sha256"]:
            raise ValueError("Pinned separation checksum changed: " + item["file"])
    if not any(
        i["file"] == "MelBandRoformer.ckpt" and i["sha256"] == WEIGHT_SHA256
        for i in config["files"]
    ):
        raise ValueError("Pinned separation checkpoint is missing")
    return config


def separate(source, output, settings):
    import torch
    import yaml
    from ml_collections import ConfigDict

    installed = runtime(verify=True, config_file=settings.get("separation_config"))
    root = Path(installed["root"])
    sys.path.insert(0, str(root / "source"))
    from models.bs_roformer import attend
    from models.bs_roformer.mel_band_roformer import MelBandRoformer
    from utils.model_utils import demix

    attention = prepare_attention(attend)
    # Only load the setup-verified upstream config, which uses a Python tuple tag.
    config = ConfigDict(yaml.load((root / "profile.yaml").read_text(), Loader=yaml.FullLoader))
    config.inference.batch_size = 1
    config.training.use_amp = settings["device"] == "cuda"

    def load_model():
        model = MelBandRoformer(**config.model)
        state = torch.load(root / "MelBandRoformer.ckpt", map_location="cpu", weights_only=True)
        model.load_state_dict(state, strict=True)
        return model.eval().to(settings["device"])

    model = inference_model(("roformer", str(root), WEIGHT_SHA256, settings["device"]), load_model)
    data, rate = sf.read(source, dtype="float32", always_2d=True)
    if rate != 44100 or data.shape[1] != 2:
        raise ValueError("RoFormer requires canonical stereo 44.1 kHz audio")
    with torch.inference_mode():
        vocals = demix(
            config, model, data.T.copy(), settings["device"], "mel_band_roformer", pbar=True
        )["vocals"].T
    if vocals.shape != data.shape or not np.isfinite(vocals).all():
        raise ValueError("RoFormer returned an invalid or misaligned waveform")
    write_stem(output / "audio/vocals.wav", vocals, rate, len(data))
    write_stem(output / "audio/instrumental.wav", data - vocals, rate, len(data))
    return {
        "backend": "mel-band-roformer-kj",
        "source_revision": SOURCE_REVISION,
        "model_revision": MODEL_REVISION,
        "weight_sha256": WEIGHT_SHA256,
        "chunk_frames": config.audio.chunk_size,
        "overlap": config.inference.num_overlap,
        "batch_size": 1,
        "mixture_consistency": True,
        "precision": "autocast-fp16" if config.training.use_amp else "fp32",
        "attention": attention,
    }
