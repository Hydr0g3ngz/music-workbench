"""Build a per-user Windows installer from the tested basic runtime and current wheel."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

from music_studio import __version__


def stage(root, base, wheel, target, sdk):
    target = target.resolve()
    if target.exists():
        raise ValueError("Use a fresh staging folder")
    shutil.copytree(base, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.log"))
    site = target / "runtime/Lib/site-packages"
    # Only stale wheel metadata in our newly copied staging tree is removed.
    for old in site.glob("music_workbench_local-*.dist-info"):
        if not old.resolve().is_relative_to(target) or old.is_symlink():
            raise ValueError("Unexpected staging metadata path")
        shutil.rmtree(old)
    with zipfile.ZipFile(wheel) as archive:
        for item in archive.infolist():
            destination = (site / item.filename).resolve()
            if not destination.is_relative_to(site.resolve()):
                raise ValueError("Invalid wheel member")
        archive.extractall(site)
    subprocess.run([
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        str(root / "scripts/build-desktop.ps1"), "-Output", str(target / "Music Workbench.exe"),
        "-Sdk", str(sdk.resolve()),
    ], check=True)
    shutil.copyfile(root / "desktop/App.cs", target / "Desktop-source.cs")
    shutil.copyfile(root / "docs/windows-install.md", target / "START-HERE.md")
    manifest = json.loads((target / "DEPENDENCIES.json").read_text(encoding="utf-8"))
    manifest["version"] = __version__
    for dependency in manifest["dependencies"]:
        if dependency["Name"] == "music-workbench-local":
            dependency["Version"] = __version__
    manifest["desktop"] = {"engine": "WebView2 Evergreen", "sdk": "1.0.4258.31"}
    (target / "DEPENDENCIES.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def compile_installer(root, payload, output, compiler, prerequisites, app_id=None):
    output.mkdir(parents=True, exist_ok=True)
    runtime = prerequisites / "MicrosoftEdgeWebView2RuntimeInstallerX64.exe"
    environment = {k: v for k, v in os.environ.items() if k != "PSModulePath"}
    subprocess.run([
        shutil.which("pwsh") or "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(root / "scripts/verify-desktop-prerequisite.ps1"),
        "-Path", str(runtime.resolve()),
    ], check=True, env=environment)
    arguments = [str(compiler.resolve()), "/Qp", "/DRepo=" + str(root),
                 "/DPayload=" + str(payload.resolve()), "/DDestination=" + str(output.resolve()),
                 "/DBuildVersion=" + __version__,
                 "/DChineseLanguage=" + str((prerequisites / "ChineseSimplified.isl").resolve()),
                 "/DWebViewInstaller=" + str(runtime.resolve())]
    if app_id:
        arguments.append("/DBuildAppId=" + app_id.strip("{}"))
    subprocess.run([*arguments, str(root / "desktop/installer.iss")], check=True)
    installer = output / f"Music-Workbench-{__version__}-Setup-x64.exe"
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    installer.with_suffix(".exe.sha256").write_text(digest + "  " + installer.name + "\n")
    print(json.dumps({"installer": str(installer), "bytes": installer.stat().st_size,
                      "sha256": digest}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--tools", type=Path, default=Path(".artifacts/desktop-build-tools"))
    parser.add_argument("--compile-only", action="store_true")
    parser.add_argument("--app-id")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    if not args.compile_only:
        if not args.base or not args.wheel:
            parser.error("Staging requires --base and --wheel")
        stage(repo, args.base, args.wheel, args.payload, args.tools / "webview2")
    compile_installer(repo, args.payload, args.dist, args.tools / "inno/ISCC.exe",
                      args.tools, args.app_id)
