from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Trim(StrictModel):
    type: Literal["trim"] = "trim"
    start: float = Field(ge=0)
    end: float = Field(gt=0)


class Gain(StrictModel):
    type: Literal["gain"] = "gain"
    db: float = Field(ge=-60, le=24)


class Fade(StrictModel):
    type: Literal["fade"] = "fade"
    in_seconds: float = Field(default=0, ge=0, le=60)
    out_seconds: float = Field(default=0, ge=0, le=60)


class Balance(StrictModel):
    type: Literal["balance"] = "balance"
    pan: float = Field(ge=-1, le=1)


class Normalize(StrictModel):
    type: Literal["normalize"] = "normalize"
    peak_dbfs: float = Field(default=-1, ge=-24, le=-0.1)


class Reverse(StrictModel):
    type: Literal["reverse"] = "reverse"


class Keep(StrictModel):
    type: Literal["keep"] = "keep"


class LoudnessNormalize(StrictModel):
    type: Literal["loudness"] = "loudness"
    target_lufs: float = Field(default=-16, ge=-36, le=-9)
    ceiling_dbtp: float = Field(default=-1, ge=-6, le=-0.1)


class MixTrack(StrictModel):
    asset: str = Field(min_length=1, max_length=80)
    gain_db: float = Field(default=0, ge=-60, le=24)
    pan: float = Field(default=0, ge=-1, le=1)


class Mix(StrictModel):
    type: Literal["mix"] = "mix"
    tracks: list[MixTrack] = Field(min_length=1, max_length=8)


Operation = Annotated[
    Trim | Gain | Fade | Balance | Normalize | Reverse | Mix | Keep | LoudnessNormalize,
    Field(discriminator="type"),
]


class PreviewRequest(StrictModel):
    revision: int = Field(ge=0)
    asset: str = Field(default="current", min_length=1, max_length=80)
    operations: list[Operation] = Field(min_length=1, max_length=24)


class RevisionRequest(StrictModel):
    revision: int = Field(ge=0)


class AdoptRequest(RevisionRequest):
    candidate: str = Field(pattern=r"^[a-f0-9]{16}$")


class ExportRequest(RevisionRequest):
    asset: str = Field(default="current", min_length=1, max_length=80)
    subtype: Literal["PCM_16", "PCM_24", "FLOAT"] = "PCM_24"


class SelectionRequest(RevisionRequest):
    asset: str = Field(default="current", min_length=1, max_length=80)
    start: float = Field(ge=0)
    end: float = Field(gt=0)


class AudioRange(StrictModel):
    start: float = Field(ge=0)
    end: float = Field(gt=0)

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("Audio range end must follow its start")
        return self


class LocalTaskRequest(RevisionRequest):
    model: str = Field(min_length=1, max_length=80)
    asset: str = Field(
        default="current",
        min_length=1,
        max_length=80,
        description="Input audio: current, source, candidate:<id> or asset:<id>. "
        "Use asset:<id> for a completed task's audio output.",
    )
    device: Literal["auto", "cpu", "cuda"] = "auto"
    range: AudioRange | None = Field(
        default=None, description="Source seconds to process; omitted means the whole asset."
    )
    alignment: Literal["auto", "native", "qwen"] = "auto"
    time_ratio: float = Field(default=1, ge=0.5, le=2)
    pitch_shift: int = Field(default=0, ge=-12, le=12)
    language: str | None = Field(default=None, min_length=2, max_length=12, pattern=r"^[a-zA-Z-]+$")
    strength: float = Field(
        default=1,
        ge=0,
        le=1,
        description="Speech cleanup only: wet/dry strength. 1 means fully processed, 0 unchanged.",
    )


class TranscriptPatch(StrictModel):
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    changes: dict[str, Annotated[str, Field(max_length=2000)]] = Field(min_length=1, max_length=500)


class CompareRequest(StrictModel):
    reference: str = Field(pattern=r"^(source|current|candidate:[a-f0-9]{16}|asset:[a-f0-9]{16})$")
    processed: str = Field(pattern=r"^(source|current|candidate:[a-f0-9]{16}|asset:[a-f0-9]{16})$")


class WeightInstallRequest(StrictModel):
    pass
