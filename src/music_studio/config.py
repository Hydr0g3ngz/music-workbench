from pathlib import Path
from typing import Literal

from platformdirs import user_data_path
from pydantic import Field

from .schema import Record


class Settings(Record):
    device: Literal["auto", "cpu", "cuda"] = "auto"
    separation_model: Literal["htdemucs", "htdemucs_ft"] = "htdemucs"
    segment_seconds: float = Field(default=6.0, ge=2, le=7.8)
    asr_model: str = "small"
    asr_revision: str | None = None
    asr_segmentation: Literal["whole", "vocal"] = "whole"
    asr_backend: Literal["whisper", "qwen", "heart"] = "whisper"
    lyrics_input: Literal["vocals", "source"] = "vocals"
    lyrics_alignment: Literal["native", "qwen", "whisper", "anchors"] = "native"
    anchor_model: Literal["small", "large-v3-turbo", "dual"] = "small"
    lyrics_python: str | None = None
    inference_python: str | None = None
    language: str | None = None
    pitch_backend: Literal["crepe", "pyin"] = "crepe"
    pitch_threshold: float = Field(default=0.35, ge=0, le=1)
    melody_decoder: Literal["classic", "stable", "rest"] = "stable"
    rhythm_backend: Literal["librosa", "librosa_percussive", "beat_this"] = "librosa_percussive"
    rhythm_checkpoint: Literal["small0", "final0", "fold2", "fold3", "fold4", "fold6"] = "small0"
    harmony_backend: Literal["stft", "cqt"] = "cqt"
    mixture_consistency: bool = True
    model_dir: str = str(user_data_path("MusicWorkbench", appauthor=False) / "AI" / "models")
    offline: bool = False
    threads: int = Field(default=4, ge=1, le=64)
    seed: int = Field(default=0, ge=0, le=4294967295)

    def resolved(self):
        value = self.model_copy(deep=True)
        value.model_dir = str(Path(self.model_dir).expanduser().resolve())
        if value.asr_backend in ("qwen", "heart"):
            from .lyric_models import MODELS

            value.asr_model, value.asr_revision = MODELS[value.asr_backend]
        if value.asr_model == "small" and value.asr_revision is None:
            value.asr_revision = "536b0662742c02347bc0e980a01041f333bce120"
        if value.asr_model in ("turbo", "large-v3-turbo") and value.asr_revision is None:
            value.asr_revision = "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf"
        if Path(value.asr_model).is_dir():
            value.asr_model = str(Path(value.asr_model).resolve())
        return value
