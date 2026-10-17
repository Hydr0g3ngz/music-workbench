"""Download pinned build inputs. Only the Inno compiler requires a local installation."""

import argparse
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

INPUTS = {
    "innosetup-6.7.3.exe": (
        "https://files.jrsoftware.org/is/6/innosetup-6.7.3.exe",
        "9c73c3bae7ed48d44112a0f48e66742c00090bdb5bef71d9d3c056c66e97b732",
    ),
    "webview2.nupkg": (
        "https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/1.0.4258.31/"
        "microsoft.web.webview2.1.0.4258.31.nupkg",
        "56f7f4b8bf9aee4b8efefbbdd4f67d5f74ebd1b100ed0806da71bf76af481aa9",
    ),
    "MicrosoftEdgeWebView2RuntimeInstallerX64.exe": (
        "https://go.microsoft.com/fwlink/?linkid=2124701",
        "3505a37b54a294c2bc423b30d6c02cd33a2e58dbcdc7e03b50d7a4112746c986",
    ),
    "ChineseSimplified.isl": (
        "https://raw.githubusercontent.com/jrsoftware/issrc/is-6_7_3/"
        "Files/Languages/Unofficial/ChineseSimplified.isl",
        "7d544b9bb1d142cfa11f2e5d3cc8abe2e55f8e066c5124e3772675aa236e1278",
    ),
}


def prepare(folder):
    folder.mkdir(parents=True, exist_ok=True)
    for name, (url, expected) in INPUTS.items():
        path = folder / name
        if not path.is_file():
            partial = path.with_suffix(path.suffix + ".part")
            with urllib.request.urlopen(url, timeout=90) as response, partial.open("wb") as out:
                while block := response.read(1024**2):
                    out.write(block)
            partial.replace(path)
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise ValueError(
                "Build input changed; review its official source before updating: " + name
            )
    sdk = folder / "webview2"
    with zipfile.ZipFile(folder / "webview2.nupkg") as archive:
        for item in archive.infolist():
            if not (sdk / item.filename).resolve().is_relative_to(sdk.resolve()):
                raise ValueError("Invalid SDK archive path")
        archive.extractall(sdk)
    (folder / "build-inputs.json").write_text(json.dumps(INPUTS, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(".artifacts/desktop-build-tools"))
    prepare(parser.parse_args().directory)
