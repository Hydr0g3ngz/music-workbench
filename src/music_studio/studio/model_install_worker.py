"""Fixed Windows tool installers, with private runtimes and real offline verification."""

import argparse
import json
import os
import threading
import urllib.request
from pathlib import Path

from ..io import read_json, sha256, write_json
from . import ai_install_worker as boot
from .model_setup import PACKS, bind_app
from .torch_download import windows_wheel

DEMUCS_SHA = "8726e21a993978c7ba086d3872e7608d7d5bfca646ca4aca459ffda844faa8b4"
CREPE_SHA = "133225604dedd2e4005f8bbd1bd0a2ec073ba8b7a6cd31ff6d5edbbfa3539986"
WHISPER_REVISION = "536b0662742c02347bc0e980a01041f333bce120"


def prepare_python(root, cache):
    archive = cache / "python-3.12.10-embed-amd64.zip"
    boot.download(boot.PYTHON_URL, archive, boot.PYTHON_SHA)
    folder = root / "env"
    python = folder / "python.exe"
    if not python.is_file():
        boot.unpack(archive, folder)
    # Write before pip bootstrap; the helper subsequently follows app upgrades.
    pth = folder / "python312._pth"
    if not pth.is_file():
        pth.touch()
    bind_app(python)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONHOME", "PYTHONPATH")}
    env.update(
        PYTHONUTF8="1",
        PYTHONUNBUFFERED="1",
        PYTHONDONTWRITEBYTECODE="1",
        PIP_DISABLE_PIP_VERSION_CHECK="1",
        PIP_CACHE_DIR=str(cache / "pip"),
        HF_HUB_DISABLE_TELEMETRY="1",
        DO_NOT_TRACK="1",
        HF_HUB_OFFLINE="0",
        TRANSFORMERS_OFFLINE="0",
    )
    with urllib.request.urlopen("https://pypi.org/pypi/pip/25.2/json", timeout=30) as response:
        metadata = json.load(response)
    wheel = next(item for item in metadata["urls"] if item["filename"].endswith(".whl"))
    pip = cache / wheel["filename"]
    boot.download(wheel["url"], pip, wheel["digests"]["sha256"])
    boot.run(
        python,
        "-c",
        "import sys,runpy;sys.path.insert(0,sys.argv.pop(1));"
        "runpy.run_module('pip',run_name='__main__')",
        pip,
        "install",
        "--no-warn-script-location",
        pip,
        env=env,
    )
    boot.run(
        python,
        "-m",
        "pip",
        "install",
        "--no-warn-script-location",
        "setuptools==80.9.0",
        "wheel==0.45.1",
        env=env,
    )
    return python, env


def install(pack, root):
    if pack not in PACKS:
        raise ValueError("Unknown fixed tool pack")
    root.mkdir(parents=True, exist_ok=True)
    cache = root / "downloads"
    cache.mkdir(exist_ok=True)

    def progress(stage, fraction):
        write_json(root / "progress.json", {"stage": stage, "fraction": fraction})
        print(stage, flush=True)

    progress("runtime", 0.02)
    python, env = prepare_python(root, cache)
    progress("dependencies", 0.1)
    if pack == "music-tools":
        wheels = [
            windows_wheel(name, "cp312", cache, version="2.5.1", flavor="cpu")
            for name in ("torch", "torchaudio")
        ]
        boot.run(python, "-m", "pip", "install", "--no-warn-script-location", *wheels, env=env)
    # Demucs and a few small pure-Python dependencies publish source distributions.
    # --no-build-isolation keeps these builds in our pinned private tool environment.
    boot.run(
        python,
        "-m",
        "pip",
        "install",
        "--no-warn-script-location",
        "--no-build-isolation",
        "-r",
        Path(__file__).with_name(pack + "-requirements.txt"),
        env=env,
    )
    boot.run(python, "-m", "pip", "check", env=env)
    progress("models", 0.5)
    models = root / "models"
    models.mkdir(exist_ok=True)
    if pack == "music-tools":
        checkpoint = models / "torch/hub/checkpoints/955717e8-8726e21a.th"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        boot.download(
            "https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/955717e8-8726e21a.th",
            checkpoint,
            DEMUCS_SHA,
        )
        crepe = python.parent / "Lib/site-packages/torchcrepe/assets/full.pth"
        if sha256(crepe) != CREPE_SHA:
            raise RuntimeError("Pinned CREPE checkpoint checksum mismatch")
        downloader = r"""
import hashlib,sys
from pathlib import Path
from huggingface_hub import HfApi,snapshot_download
repo='Systran/faster-whisper-small'
revision,cache=sys.argv[1:]
names=['config.json','model.bin','tokenizer.json','vocabulary.txt']
folder=Path(snapshot_download(repo,revision=revision,cache_dir=cache,allow_patterns=names))
metadata=HfApi().model_info(repo,revision=revision,files_metadata=True)
items={i.rfilename:i for i in metadata.siblings}
for name in names:
    path=folder/name
    item=items[name]
    if item.lfs:
        with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=item.lfs.sha256:raise RuntimeError('Whisper checkpoint checksum mismatch')
    else:
        raw=path.read_bytes()
        actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if actual!=item.blob_id:raise RuntimeError('Whisper configuration checksum mismatch')
"""
        boot.run(
            python, "-X", "utf8", "-c", downloader, WHISPER_REVISION, models / "whisper", env=env
        )
        snapshot = models / (
            "whisper/models--Systran--faster-whisper-small/snapshots/" + WHISPER_REVISION
        )
        files = [
            checkpoint,
            crepe,
            *(
                snapshot / n
                for n in ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")
            ),
        ]
    else:
        from .cleanup import download

        files = [download(models, model) for model in PACKS[pack]["models"]]
    manifest = [{"file": str(p.relative_to(root)), "sha256": sha256(p)} for p in files]
    progress("verify", 0.8)
    offline = {
        **env,
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "TORCH_HOME": str(models / "torch"),
    }
    boot.run(
        python,
        "-X",
        "utf8",
        "-m",
        "music_studio.studio.model_verify",
        "--pack",
        pack,
        "--root",
        root,
        env=offline,
    )
    verification = read_json(root / "verification/report.json")
    if set(verification) != set(PACKS[pack]["models"]):
        raise RuntimeError("Tool verification is incomplete")
    # Publish atomically only after every capability produced valid output offline.
    write_json(
        root / "runtime.json",
        {
            "schema": 1,
            "pack": pack,
            "python": str(python),
            "model_dir": str(models),
            "device": "cpu",
            "files": manifest,
            "verification": verification,
        },
    )
    progress("complete", 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", choices=PACKS, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--owner-pid", type=int)
    args = parser.parse_args()
    if args.owner_pid:
        threading.Thread(target=boot.watch_backend, args=(args.owner_pid,), daemon=True).start()
    install(args.pack, args.root.resolve())
