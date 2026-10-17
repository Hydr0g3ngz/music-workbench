"""Explicit ACE-Step setup. UI startup never downloads models or changes its Python."""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import venv
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO / ".artifacts/acestep")
    parser.add_argument("--environment", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--checkpoints", type=Path)
    parser.add_argument(
        "--skip-install", action="store_true", help="Verify an existing environment"
    )
    parser.add_argument(
        "--runtime-file", type=Path, default=REPO / ".artifacts/acestep-runtime.json"
    )
    args = parser.parse_args()
    if sys.version_info[:2] not in ((3, 11), (3, 12)):
        raise RuntimeError("Run this script with Python 3.11 or 3.12")
    if platform.system() not in ("Windows", "Linux") or platform.machine().lower() not in (
        "amd64",
        "x86_64",
    ):
        raise RuntimeError(
            "This first creation profile supports Windows/Linux x64 with NVIDIA CUDA"
        )
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    environment = (args.environment or root / "env").resolve()
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        if args.skip_install:
            raise RuntimeError("The requested Python environment does not exist")
        venv.EnvBuilder(with_pip=True).create(environment)
    if not args.skip_install:
        installed_torch = subprocess.run(
            [
                str(python),
                "-c",
                "import importlib.metadata as m; "
                "print(m.version('torch')+'|'+m.version('torchaudio'))",
            ],
            capture_output=True,
            text=True,
        )
        torch_ready = installed_torch.stdout.strip() == "2.10.0+cu128|2.10.0+cu128"
        if os.name == "nt" and not torch_ready:
            from download_pytorch import windows_wheel

            tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
            wheels = [windows_wheel(p, tag, root / "wheels") for p in ("torch", "torchaudio")]
            run(python, "-m", "pip", "install", *wheels)
        elif not torch_ready:
            run(
                python,
                "-m",
                "pip",
                "install",
                "torch==2.10.0",
                "torchaudio==2.10.0",
                "--index-url",
                "https://download.pytorch.org/whl/cu128",
            )
        run(python, "-m", "pip", "install", "-r", REPO / "requirements/acestep.txt")
    source = (args.source or root / ("source-" + SOURCE)).resolve()
    install_source(source, root / ("source-" + SOURCE + ".zip"))
    checkpoints = (args.checkpoints or REPO / ".cache/models/acestep15" / MODEL).resolve()
    checkpoints.mkdir(parents=True, exist_ok=True)
    # This subprocess uses the isolated environment's pinned Hub client, not the UI Python.
    downloader = r"""
import hashlib,json,sys
from pathlib import Path
from huggingface_hub import HfApi,snapshot_download
revision,folder=sys.argv[1:]
patterns=['acestep-v15-turbo/*','vae/*','Qwen3-Embedding-0.6B/*','README.md']
snapshot_download('ACE-Step/Ace-Step1.5',revision=revision,local_dir=folder,allow_patterns=patterns)
metadata=HfApi().model_info('ACE-Step/Ace-Step1.5',revision=revision,files_metadata=True)
expected={f.rfilename:f for f in metadata.siblings}
files=[]
for name,item in expected.items():
    path=Path(folder)/name
    if not path.is_file():continue
    with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if item.lfs and actual!=item.lfs.sha256:
        raise RuntimeError('Checkpoint checksum mismatch: '+name)
    if not item.lfs and item.blob_id:
        raw=path.read_bytes()
        git_hash=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if git_hash!=item.blob_id:raise RuntimeError('Checkpoint metadata changed: '+name)
    files.append({'file':name,'bytes':path.stat().st_size,'sha256':actual})
Path(folder,'music-studio-manifest.json').write_text(json.dumps({'revision':revision,'files':files},indent=2))
print('Verified',len(files),'checkpoint files',sum(f['bytes'] for f in files),'bytes')
"""
    run(python, "-X", "utf8", "-c", downloader, MODEL, checkpoints)
    model_view = prepare_model_view(source, checkpoints)
    child = os.environ.copy()
    child.update(
        PYTHONPATH=os.pathsep.join((str(source), str(REPO / "src"))),
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        GRADIO_ANALYTICS_ENABLED="False",
    )
    run(
        python,
        "-X",
        "utf8",
        "-c",
        "from music_studio.studio.windows_dlls import prepare_torch; prepare_torch(); "
        "import torch; from acestep.handler import AceStepHandler; "
        "from acestep.inference import generate_music; "
        "from torchao.quantization import quantize_, Int8WeightOnlyConfig; "
        "assert torch.cuda.is_available(), 'NVIDIA CUDA is unavailable'; "
        "assert torch.ones(1, device='cuda').sum().item() == 1; "
        "model=torch.nn.Linear(128,128,dtype=torch.bfloat16); "
        "quantize_(model,Int8WeightOnlyConfig()); model.to('cuda'); "
        "assert torch.isfinite(model(torch.ones(1,128,device='cuda',dtype=torch.bfloat16))).all(); "
        "print('CUDA:',torch.cuda.get_device_name(),'Torch:',torch.__version__)",
        env=child,
    )
    freeze = subprocess.check_output([str(python), "-m", "pip", "freeze"], text=True)
    lock = root / "requirements.lock.txt"
    lock.write_text(freeze, encoding="utf-8")
    config = {
        "python": str(python),
        "source": str(source),
        "checkpoints": str(model_view),
        "download_snapshot": str(checkpoints),
        "source_revision": SOURCE,
        "model_revision": MODEL,
        "source_archive_sha256": ARCHIVE_SHA256,
        "weights_manifest_sha256": digest(model_view / "music-studio-manifest.json"),
        "environment_lock": str(lock),
        "profile": "cuda-auto-v4-pread",
        "quantization_policy": "gpu-free-memory",
    }
    args.runtime_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.runtime_file.with_suffix(".tmp")
    temporary.write_text(json.dumps(config, indent=2), encoding="utf-8")
    temporary.replace(args.runtime_file)
    print("Ready. Restart the Create workbench. Runtime:", args.runtime_file)
    print("Try a 12–20 second, 8-step instrumental draft first; longer drafts may exceed VRAM.")


if __name__ == "__main__":
    main()
