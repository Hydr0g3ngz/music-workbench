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
        "desktop/App.cs",
        "desktop/app.manifest",
        "desktop/installer.iss",
        "desktop/installation-info.txt",
        "scripts/build-desktop.ps1",
        "scripts/package_installer.py",
        "scripts/prepare_installer_tools.py",
        "scripts/verify-desktop-prerequisite.ps1",
        "docs/windows-install.md",
        "src/music_studio/studio/ai_setup.py",
        "src/music_studio/studio/ai_install_worker.py",
        "src/music_studio/studio/ace_setup.py",
        "src/music_studio/studio/ace-requirements.txt",
        "src/music_studio/studio/torch_download.py",
        "src/music_studio/ui/static/ai-setup.html",
        "src/music_studio/ui/static/ai-setup.js",
        "src/music_studio/ui/static/ai-setup.css",
        "src/music_studio/ui/static/station-tutorial.js",
        "src/music_studio/ui/static/station-tutorial.css",
        "src/music_studio/ui/static/learn.html",
        "src/music_studio/ui/static/learn.js",
        "src/music_studio/ui/static/learn.css",
        "docs/first-sketch.md",
        "docs/launch-kit.md",
        "docs/images/first-sketch-demo.gif",
        "scripts/make_demo_video.py",
        "desktop/Launcher.cs",
        "scripts/build-launcher.ps1",
        "scripts/package_portable.py",
        "scripts/verify_portable.py",
        "docs/desktop-start.md",
        "docs/volume-and-repaint.md",
        "docs/images/welcome-zh.png",
        "docs/images/welcome-en.png",
        "src/music_studio/desktop.py",
        "src/music_studio/ui/static/welcome.html",
        "src/music_studio/ui/static/station-envelope-ui.js",
        "src/music_studio/studio/repaint.py",
        "Start-Music-Workbench.cmd",
        "src/music_studio/ui/static/station-edit.js",
        "src/music_studio/ui/static/station-workflow.js",
        "src/music_studio/ui/static/station-workflow.css",
        "src/music_studio/ui/static/station-composition.js",
        "src/music_studio/ui/static/station-composition-ui.js",
        "src/music_studio/ui/static/station-composition.css",
        "src/music_studio/studio/composition.py",
        "docs/arranging-methods.md",
        "docs/arranging-validation.md",
        "src/music_studio/studio/fitting.py",
        "src/music_studio/studio/audition.py",
        "src/music_studio/ui/static/station-fit.js",
        "src/music_studio/ui/static/station-fit-ui.js",
        "src/music_studio/ui/static/station-audition-ui.js",
        "src/music_studio/ui/static/station-material.css",
        "docs/material-fitting.md",
        "docs/images/material-fit-zh.png",
        "docs/images/material-ab-zh.png",
        "scripts/benchmark_material_fit.py",
        "src/music_studio/studio/project_pack.py",
        "src/music_studio/studio/musical.py",
        "docs/ai-production-workflow.md",
        "docs/creations/radio-through-the-clouds.md",
        "src/music_studio/ui/static/station-timing.js",
        "src/music_studio/ui/static/station-timing-ui.js",
        "src/music_studio/ui/static/station-timing.css",
        "docs/timing.md",
        "docs/timing.en.md",
        "docs/timing-validation.md",
        "docs/images/timing-zh.png",
        "docs/images/timing-en.png",
        "src/music_studio/ui/static/station-recorder.js",
        "src/music_studio/ui/static/station-recorder-worklet.js",
        "src/music_studio/ui/static/station-recording-ui.js",
        "src/music_studio/ui/static/station-recording.css",
        "docs/recording.md",
        "docs/recording.en.md",
        "Start-Music-Studio.cmd",
        "QUICKSTART.md",
        "scripts/launch.ps1",
        "scripts/launch-workbench.ps1",
        "src/music_studio/ui/navigation.py",
        "src/music_studio/ui/static/workbench-navigation.js",
        "src/music_studio/ui/static/workbench-icon.svg",
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
        "src/music_studio/studio/routing.py",
        "src/music_studio/studio/polyphony.py",
        "src/music_studio/studio/piano_notes.py",
        "src/music_studio/studio/piano-notes-requirements.txt",
        "src/music_studio/ui/static/station-note-tools.js",
        "src/music_studio/ui/static/station-note-tools-ui.js",
        "src/music_studio/ui/static/updates.html",
        "src/music_studio/ui/static/updates.js",
        "docs/note-editing.md",
        "docs/note-editing.en.md",
        "docs/piano-notes.md",
        "docs/piano-notes.en.md",
        "docs/piano-benchmark.md",
        "docs/dev21-validation.md",
        "docs/releases/v0.2.0.dev21.md",
        "docs/creations/after-the-rain.md",
        "scripts/benchmark_piano.py",
        "benchmarks/data-manifests/smd-v2-piano.json",
        "benchmarks/reports/piano-v1.json",
        "benchmarks/reports/after-the-rain-v1.json",
        "src/music_studio/studio/polyphonic-notes-requirements.txt",
        "src/music_studio/ui/static/station-groups.js",
        "src/music_studio/ui/static/station-routing.js",
        "src/music_studio/ui/static/station-production-ui.js",
        "src/music_studio/ui/static/station-production.css",
        "docs/groups-and-routing.md",
        "docs/groups-and-routing.en.md",
        "docs/polyphonic-notes.md",
        "docs/polyphonic-notes.en.md",
        "docs/polyphony-benchmark.md",
        "scripts/benchmark_polyphony.py",
        "benchmarks/reports/polyphony-v1.json",
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
