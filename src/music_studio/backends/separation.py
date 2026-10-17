from pathlib import Path

import numpy as np
import soundfile as sf

from ..audio import write_stem


def separate(source: Path, output: Path, config: dict) -> dict:
    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model

    torch.manual_seed(config.get("seed", 0))
    model = get_model(config["separation_model"])
    model.eval()
    data, rate = sf.read(source, dtype="float32", always_2d=True)
    if model.samplerate != rate or model.audio_channels != data.shape[1]:
        raise ValueError("This backend requires a stereo 44.1 kHz Demucs model")
    wave = torch.from_numpy(data.T.copy())
    reference = wave.mean(0)
    mean, std = reference.mean(), reference.std()
    segment = config["segment_seconds"]
    warnings = []
    four_stems = config.get("four_stems", False)
    if not torch.isfinite(std) or std < 1e-8:
        vocals = np.zeros_like(data)
        accompaniment = data
        stems = {
            role: (data if role == "other" else np.zeros_like(data))
            for role in ("drums", "bass", "vocals", "other")
        }
    else:
        normalized = (wave - mean) / std
        while True:
            try:
                with torch.inference_mode():
                    estimates = apply_model(
                        model,
                        normalized[None],
                        device=config["device"],
                        shifts=0,
                        split=True,
                        segment=segment,
                        overlap=0.25,
                        progress=True,
                        num_workers=0,
                    )[0].cpu()
                break
            except torch.cuda.OutOfMemoryError:
                if segment <= 2:
                    raise RuntimeError(
                        "GPU memory exhausted at 2-second chunks. "
                        "Close GPU apps or use --device cpu."
                    ) from None
                segment = max(2.0, segment / 2)
                torch.cuda.empty_cache()
                warnings.append(f"CUDA OOM: retried separation with {segment}s chunks")
        estimates = estimates * std + mean
        index = model.sources.index("vocals")
        vocals = estimates[index].numpy().T
        others = [i for i in range(len(model.sources)) if i != index]
        accompaniment = estimates[others].sum(0).numpy().T
        if config.get("mixture_consistency"):
            # Residual accompaniment preserves exact mixture reconstruction and timing.
            accompaniment = data - vocals
        stems = {role: estimates[i].numpy().T for i, role in enumerate(model.sources)}
        if four_stems and config.get("mixture_consistency"):
            stems["other"] += data - sum(stems.values())
    if four_stems:
        for role, values in stems.items():
            write_stem(output / f"audio/{role}.wav", values, rate, len(data))
        return {
            "backend": "demucs",
            "model": config["separation_model"],
            "segment_seconds": segment,
            "warnings": warnings,
            "mixture_consistency": config.get("mixture_consistency", False),
            "files": [f"audio/{role}.wav" for role in stems],
        }
    write_stem(output / "audio/vocals.wav", vocals, rate, len(data))
    write_stem(output / "audio/instrumental.wav", accompaniment, rate, len(data))
    return {
        "backend": "demucs",
        "model": config["separation_model"],
        "segment_seconds": segment,
        "mixture_consistency": config.get("mixture_consistency", False),
        "warnings": warnings,
        "files": ["audio/vocals.wav", "audio/instrumental.wav"],
    }
