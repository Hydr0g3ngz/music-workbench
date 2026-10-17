"""Fixed model assets with revision, content checksums and resumable HTTP downloads."""

import hashlib
import json
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from ..io import sha256, write_json
from ..lyric_models import MODELS
from . import ai_install_worker as boot
from .separation import MODEL_REVISION, SOURCE_REVISION, WEIGHT_SHA256

SOURCE_SHA = "fa62b1ff7602e1dcaef1234274ad0ca4eafbea4c7c02554b1b8b5c64544cee9d"


def download_file(url, path, size, expected, *, git_blob=False):
    """Only append a response that proves its byte offset. Publish after verification."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    def valid(candidate):
        if not candidate.is_file() or candidate.stat().st_size != size:
            return False
        if git_blob:
            raw = candidate.read_bytes()
            return (
                hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                == expected
            )
        return sha256(candidate) == expected

    if valid(path):
        return path
    partial = path.with_suffix(path.suffix + ".download")
    for attempt in range(4):
        offset = partial.stat().st_size if partial.is_file() else 0
        if offset >= size:
            if valid(partial):
                partial.replace(path)
                return path
            partial.unlink()
            offset = 0
        try:
            request = urllib.request.Request(
                url, headers={"Range": f"bytes={offset}-"} if offset else {}
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                append = offset and response.status == 206
                if (
                    append
                    and response.headers.get("Content-Range") != f"bytes {offset}-{size - 1}/{size}"
                ):
                    raise ValueError("Unexpected model download byte range")
                if response.status not in (200, 206):
                    raise ValueError("Unexpected model download response")
                if (
                    response.status == 206
                    and not offset
                    and response.headers.get("Content-Range") != f"bytes 0-{size - 1}/{size}"
                ):
                    raise ValueError("Incomplete model download byte range")
                received = offset if append else 0
                with partial.open("ab" if append else "wb") as output:
                    while block := response.read(1024**2):
                        received += len(block)
                        if received > size:
                            raise ValueError("Model download exceeded pinned file size")
                        output.write(block)
            if not valid(partial):
                raise ValueError("Model download size or checksum mismatch: " + path.name)
            partial.replace(path)
            return path
        except (OSError, ValueError):
            if attempt == 3:
                raise
            time.sleep(attempt + 1)
    raise RuntimeError("Model download did not finish")


def lyric_snapshot(name, models):
    repo, revision = MODELS[name]
    with urllib.request.urlopen(
        f"https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true", timeout=60
    ) as response:
        metadata = json.load(response)
    if metadata["sha"] != revision:
        raise ValueError("Model revision changed")
    folder = (models / "lyrics" / name / revision).resolve()
    files = []
    for item in metadata["siblings"]:
        filename = item["rfilename"]
        if not filename.endswith((".json", ".txt", ".safetensors")):
            continue
        path = (folder / filename).resolve()
        if not path.is_relative_to(folder):
            raise ValueError("Invalid pinned model filename")
        lfs = item.get("lfs")
        print("Model file: " + name + "/" + filename, flush=True)
        download_file(
            f"https://huggingface.co/{repo}/resolve/{revision}/"
            + urllib.parse.quote(filename, safe="/")
            + "?download=true",
            path,
            lfs["size"] if lfs else item["size"],
            lfs["sha256"] if lfs else item["blobId"],
            git_blob=not bool(lfs),
        )
        files.append(path)
    if not any(p.suffix == ".safetensors" for p in files) or not (folder / "config.json").is_file():
        raise ValueError("Pinned model snapshot is incomplete")
    ready = folder / "model-ready.json"
    write_json(
        ready,
        {"repository": repo, "revision": revision, "sha256": {p.name: sha256(p) for p in files}},
    )
    return [*files, ready]


def roformer_assets(root, python, cache):
    archive = cache / "roformer-source.zip"
    boot.download(
        f"https://codeload.github.com/ZFTurbo/Music-Source-Separation-Training/zip/{SOURCE_REVISION}",
        archive,
        SOURCE_SHA,
    )
    model_root = root / "models"
    source = (model_root / "source").resolve()
    with zipfile.ZipFile(archive) as package:
        prefix = f"Music-Source-Separation-Training-{SOURCE_REVISION}/"
        for item in package.infolist():
            if item.is_dir() or not item.filename.startswith(prefix):
                continue
            relative = Path(item.filename[len(prefix) :])
            if relative.parts[0] not in ("models", "utils", "configs", "LICENSE"):
                continue
            target = (source / relative).resolve()
            if not target.is_relative_to(source):
                raise ValueError("Invalid RoFormer source path")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(package.read(item))
    profile = model_root / "profile.yaml"
    profile.write_bytes(
        (source / "configs/KimberleyJensen/config_vocals_mel_band_roformer_kj.yaml").read_bytes()
    )
    checkpoint = model_root / "MelBandRoformer.ckpt"
    # The fixed model card's checkpoint is immutable and verified against a pinned SHA.
    boot.download(
        f"https://huggingface.co/KimberleyJSN/melbandroformer/resolve/{MODEL_REVISION}/MelBandRoformer.ckpt",
        checkpoint,
        WEIGHT_SHA256,
    )
    files = [profile, checkpoint, *sorted(source.rglob("*.py"))]
    config_file = root / "separation-runtime.json"
    write_json(
        config_file,
        {
            "python": str(python),
            "root": str(model_root),
            "source_revision": SOURCE_REVISION,
            "model_revision": MODEL_REVISION,
            "files": [
                {"file": p.relative_to(model_root).as_posix(), "sha256": sha256(p)} for p in files
            ],
        },
    )
    return [*files, config_file], {"separation_config": str(config_file)}
