"""Explicit ACE-Step setup. UI startup never downloads models or changes its Python."""

import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = "ca1e85fe9430179831e6bc6be790c332190a3866"
ARCHIVE_SHA256 = "108e45dffc7eb62af98d781c4159aa63a2b7a241186734e3e065279da7fc198d"
MODEL = "19671f406d603126926c1b7e2adc169acbcade22"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(*args, **kwargs):
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def install_source(directory, archive):
    if not archive.is_file():
        print("Downloading pinned ACE-Step source (~9 MB)", flush=True)
        with (
            urllib.request.urlopen(
                f"https://codeload.github.com/ACE-Step/ACE-Step-1.5/zip/{SOURCE}", timeout=60
            ) as response,
            archive.with_suffix(".part").open("wb") as output,
        ):
            while block := response.read(1024 * 1024):
                output.write(block)
        archive.with_suffix(".part").replace(archive)
    if digest(archive) != ARCHIVE_SHA256:
        raise RuntimeError("ACE-Step source archive checksum mismatch; retained for inspection")
    with zipfile.ZipFile(archive) as package:
        for entry in package.infolist():
            if entry.is_dir():
                continue
            relative = Path(*Path(entry.filename).parts[1:])
            if not relative.parts or (
                relative.parts[0] != "acestep"
                and str(relative) not in ("LICENSE", "README.md", "pyproject.toml")
            ):
                continue
            target = (directory / relative).resolve()
            if not target.is_relative_to(directory.resolve()):
                raise RuntimeError("Invalid source archive path")
            raw = package.read(entry)
            if target.is_file() and target.read_bytes() != raw:
                raise RuntimeError(f"Existing source differs from the pinned version: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)


def prepare_model_view(source, snapshot):
    """Pin upstream's model-code sync without modifying the downloaded snapshot."""
    original = json.loads((snapshot / "music-studio-manifest.json").read_text(encoding="utf-8"))
    desired = {}
    for item in original["files"]:
        path = (snapshot / item["file"]).resolve()
        if not path.is_relative_to(snapshot.resolve()):
            raise RuntimeError("Invalid checkpoint manifest path")
        desired[item["file"]] = (path, item["sha256"], "checkpoint")
    code = list((source / "acestep/models/turbo").glob("*.py"))
    if not code:
        raise RuntimeError("Pinned ACE-Step model implementation is missing")
    for path in code:
        if path.name != "__init__.py":
            desired["acestep-v15-turbo/" + path.name] = (path, digest(path), "source")
    view = snapshot.with_name(snapshot.name + "-code-" + SOURCE[:12])
    if view.is_symlink():
        raise RuntimeError("Invalid resolved checkpoint directory")
    view.mkdir(exist_ok=True)
    files = []
    for name in sorted(desired):
        source_file, expected, origin = desired[name]
        target = (view / name).resolve()
        if not target.is_relative_to(view.resolve()):
            raise RuntimeError("Invalid resolved checkpoint path")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file():
            if digest(target) != expected:
                raise RuntimeError(f"Resolved checkpoint changed: {target}")
        elif source_file.suffix == ".safetensors":
            try:
                os.link(source_file, target)
            except OSError:
                shutil.copy2(source_file, target)
        else:
            shutil.copy2(source_file, target)
        files.append(
            {
                "file": name,
                "sha256": expected,
                "bytes": source_file.stat().st_size,
                "origin": origin,
            }
        )
    manifest = view / "music-studio-manifest.json"
    temporary = manifest.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {
                "model_revision": MODEL,
                "source_revision": SOURCE,
                "files": files,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary.replace(manifest)
    print("Pinned model implementation prepared:", view, flush=True)
    return view
