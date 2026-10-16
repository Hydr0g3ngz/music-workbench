"""Build wheel/sdist and a Windows source+wheel preview ZIP, with SHA-256 sums."""

import argparse
import hashlib
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

from music_studio import __version__


def package(root: Path, dist: Path, *, build=True):
    dist.mkdir(parents=True, exist_ok=True)
    if build:
        subprocess.run([sys.executable, "-m", "build", "--outdir", str(dist)], cwd=root, check=True)
    wheel = dist / f"music_workbench_local-{__version__}-py3-none-any.whl"
    source = dist / f"music_workbench_local-{__version__}.tar.gz"
    archive = dist / f"Music-Workbench-{__version__}-Windows.zip"
    prefix = f"Music-Workbench-{__version__}"
    with (
        tarfile.open(source) as tar,
        zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output,
    ):
        for member in tar.getmembers():
            if not member.isfile():
                continue
            relative = PurePosixPath(*PurePosixPath(member.name).parts[1:])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Unexpected source archive member: {member.name}")
            data = tar.extractfile(member).read()
            output.writestr(f"{prefix}/{relative}", data)
        output.write(wheel, f"{prefix}/packages/{wheel.name}")
    for required in (
        "Start-Music-Workbench.cmd",
        "Start-Music-Studio.cmd",
        "QUICKSTART.md",
        "scripts/launch.ps1",
        "Start-Music-Studio-Next.cmd",
        "scripts/launch-next.ps1",
        "scripts/setup-next.ps1",
        "scripts/setup-next-models.ps1",
        "scripts/setup-next-cleanup.ps1",
        "Start-Music-Studio-Create.cmd",
        "scripts/setup_ace.py",
        "scripts/setup_separation.py",
        "scripts/download_pytorch.py",
        "requirements/acestep.txt",
        "src/music_studio/ui/static/station.html",
        "src/music_studio/ui/static/station.js",
        "src/music_studio/ui/static/station-engine.js",
        "src/music_studio/ui/static/effects-dsp.js",
        "src/music_studio/ui/static/station-worklet.js",
        "src/music_studio/ui/static/station-effects.css",
        "src/music_studio/studio/effects.py",
        "docs/mixing.md",
        "docs/mixing.en.md",
        "src/music_studio/ui/static/station-library.css",
        "src/music_studio/data/creation/manifest.json",
        "src/music_studio/data/creation/NOTICE.md",
        "docs/creation-library.md",
        "docs/creation-library.en.md",
        "docs/music-generation.md",
        "docs/music-generation.en.md",
        "src/music_studio/ui/static/comparison.js",
        "src/music_studio/ui/speech_demo/noisy.flac",
        "src/music_studio/ui/speech_demo/ATTRIBUTION.md",
        "src/music_studio/ui/speech_demo/manifest.json",
        "src/music_studio/studio/licenses/DPDFNet-Apache-2.0.txt",
        "src/music_studio/studio/licenses/GTCRN-MIT.txt",
        "docs/speech-cleanup.md",
        "docs/speech-cleanup.en.md",
        "docs/next-preview.md",
        "docs/next-preview.en.md",
        "docs/next-models.md",
        "docs/next-models.en.md",
    ):
        with zipfile.ZipFile(archive) as output:
            if f"{prefix}/{required}" not in output.namelist():
                raise ValueError(f"Release is missing {required}")
    pack = "music_studio/data/creation/"
    with zipfile.ZipFile(wheel) as built, zipfile.ZipFile(archive) as bundled:
        manifest = json.loads(built.read(pack + "manifest.json"))
        if len(manifest["samples"]) != 23:
            raise ValueError("Factory sample pack is incomplete")
        for sample in manifest["samples"]:
            expected = sample["sha256"]
            copies = (
                built.read(pack + sample["file"]),
                bundled.read(f"{prefix}/src/{pack}{sample['file']}"),
            )
            if any(hashlib.sha256(raw).hexdigest() != expected for raw in copies):
                raise ValueError("Factory sample changed in release: " + sample["file"])
    files = [archive, wheel, source]
    checksums = dist / "SHA256SUMS.txt"
    checksums.write_text(
        "".join(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in files
        ),
        encoding="ascii",
        newline="\n",
    )
    print("Built release (Python required; neural weights not bundled):")
    for path in [*files, checksums]:
        print(f"  {path.name}  {path.stat().st_size:,} bytes")
    return files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    package(root, args.dist.resolve(), build=not args.skip_build)
