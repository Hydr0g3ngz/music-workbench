"""Pinned, local-first lyric models. Weights are never bundled with the application."""

from pathlib import Path

MODELS = {
    "qwen": ("Qwen/Qwen3-ASR-1.7B", "7278e1e70fe206f11671096ffdd38061171dd6e5"),
    "aligner": (
        "Qwen/Qwen3-ForcedAligner-0.6B",
        "c7cbfc2048c462b0d63a45797104fc9db3ad62b7",
    ),
    "heart": (
        "HeartMuLa/HeartTranscriptor-oss",
        "918f88917c17489c1f8dbae0165cd1019c4d5cd3",
    ),
}


def model_path(name: str, config: dict) -> str:
    from huggingface_hub import snapshot_download

    repository, revision = MODELS[name]
    local = Path(config["model_dir"]) / "lyrics" / name / revision
    if (local / "model-ready.json").is_file():
        from .io import read_json

        manifest = read_json(local / "model-ready.json")
        if manifest.get("revision") == revision and manifest.get("repository") == repository:
            if all((local / item).is_file() for item in manifest["sha256"]):
                return str(local.resolve())
    try:
        return snapshot_download(
            repository,
            revision=revision,
            cache_dir=str(Path(config["model_dir"]) / "huggingface"),
            local_files_only=config["offline"],
            max_workers=3,
        )
    except Exception as error:
        raise RuntimeError(
            f"Cannot load {repository}@{revision[:8]}. "
            "Install or repair this tool in AI setup, or configure its optional local runtime."
        ) from error


def runtime_python(config: dict) -> str | None:
    if config.get("asr_backend", "whisper") == "whisper" and config.get(
        "lyrics_alignment", "native"
    ) in ("native", "anchors", "whisper"):
        return None
    configured = config.get("lyrics_python")
    if configured:
        path = Path(configured).expanduser().resolve()
        if not path.is_file():
            raise RuntimeError(f"Lyric runtime Python does not exist: {path}")
        return str(path)
    return None


def runtime_identity(config: dict) -> dict:
    import json
    import os
    import subprocess
    import sys

    python = runtime_python(config) or sys.executable
    script = """import importlib.metadata as m, json, sys
names=['faster-whisper','ctranslate2','torch','transformers','qwen-asr']
versions={}
for name in names:
    try: versions[name]=m.version(name)
    except m.PackageNotFoundError: versions[name]=None
print(json.dumps({'python':sys.version,'packages':versions}))
"""
    result = subprocess.run(
        [python, "-c", script],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    return json.loads(result.stdout)
