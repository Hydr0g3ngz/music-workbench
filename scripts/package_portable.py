"""Bundle an application-local CPython runtime and wheels, without bundling model weights."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from music_studio import __version__

PYTHON_URL = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"
PYTHON_SHA256 = "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"


def package(root, dist, wheel, runtime_zip):
    dist.mkdir(parents=True, exist_ok=True)
    folder = dist / f"Music-Workbench-{__version__}-Windows-Portable"
    if folder.exists():
        raise ValueError("Use a fresh output directory; existing packages are never overwritten")
    if not runtime_zip.exists():
        urllib.request.urlretrieve(PYTHON_URL, runtime_zip)
    if hashlib.sha256(runtime_zip.read_bytes()).hexdigest() != PYTHON_SHA256:
        raise ValueError("CPython runtime checksum mismatch")
    runtime = folder / "runtime"
    runtime.mkdir(parents=True)
    with zipfile.ZipFile(runtime_zip) as archive:
        for item in archive.infolist():
            target = (runtime / item.filename).resolve()
            if not target.is_relative_to(runtime.resolve()):
                raise ValueError("Invalid runtime archive path")
        archive.extractall(runtime)
    (runtime / "python312._pth").write_text(
        "python312.zip\n.\nLib/site-packages\nimport site\n", encoding="utf-8"
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--only-binary=:all:",
            "--platform",
            "win_amd64",
            "--python-version",
            "3.12",
            "--implementation",
            "cp",
            "--abi",
            "cp312",
            "--target",
            str(runtime / "Lib/site-packages"),
            str(wheel.resolve()) + "[workstation]",
        ],
        check=True,
    )
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(root / "scripts/build-launcher.ps1"),
            "-Output",
            str(folder / "Music Workbench.exe"),
        ],
        check=True,
    )
    shutil.copyfile(root / "LICENSE", folder / "LICENSE")
    shutil.copyfile(root / "docs/desktop-start.md", folder / "START-HERE.md")
    shutil.copyfile(root / "desktop/Launcher.cs", folder / "Launcher-source.cs")
    manifest = {
        "version": __version__,
        "python_url": PYTHON_URL,
        "python_sha256": PYTHON_SHA256,
        "dependencies": [],
    }
    for metadata in sorted((runtime / "Lib/site-packages").glob("*.dist-info/METADATA")):
        lines = metadata.read_text(encoding="utf-8").splitlines()
        fields = dict(
            line.split(": ", 1) for line in lines if line.startswith(("Name: ", "Version: "))
        )
        manifest["dependencies"].append(fields)
    (folder / "DEPENDENCIES.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    archive = dist / (folder.name + ".zip")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for path in sorted(folder.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                output.write(path, path.relative_to(folder.parent))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(digest + "  " + archive.name + "\n")
    print(json.dumps({"archive": str(archive), "sha256": digest, "bytes": archive.stat().st_size}))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dist", type=Path, required=True)
    p.add_argument("--wheel", type=Path, required=True)
    p.add_argument(
        "--runtime-zip", type=Path, default=Path(".artifacts/python-3.12.10-embed-amd64.zip")
    )
    a = p.parse_args()
    package(Path(__file__).resolve().parents[1], a.dist.resolve(), a.wheel, a.runtime_zip)
