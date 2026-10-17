"""Fixed ACE-Step installer. No user-provided executable, URL or package arguments."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

from ..io import read_json, write_json
from .ace_setup import ARCHIVE_SHA256, MODEL, SOURCE, digest, install_source, prepare_model_view
from .process import stop_owned_process
from .torch_download import windows_wheel

PYTHON_URL = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"
PYTHON_SHA = "4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3"
active_child = None


def download(url, path, expected):
    if path.is_file() and digest(path) == expected:
        return
    partial = path.with_suffix(path.suffix + ".part")
    with urllib.request.urlopen(url, timeout=60) as response, partial.open("wb") as output:
        shutil.copyfileobj(response, output, 1024**2)
    if digest(partial) != expected:
        raise RuntimeError("Downloaded file checksum mismatch: " + path.name)
    partial.replace(path)


def unpack(archive, folder):
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as package:
        for item in package.infolist():
            if not (folder / item.filename).resolve().is_relative_to(folder.resolve()):
                raise ValueError("Invalid runtime archive path")
        package.extractall(folder)


def run(python, *args, env=None):
    global active_child
    active_child = subprocess.Popen(
        [str(python), *map(str, args)],
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=sys.stdout,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        start_new_session=os.name != "nt",
    )
    code = active_child.wait()
    active_child = None
    if code:
        raise RuntimeError(f"AI component exited {code}: {args[0]}")


def watch_backend(pid):
    from .task_worker import owner_alive

    while owner_alive(pid):
        time.sleep(1)
    if active_child:
        stop_owned_process(active_child)
    os._exit(130)


def install(root):
    root.mkdir(parents=True, exist_ok=True)
    cache = root / "downloads"
    cache.mkdir(exist_ok=True)

    def progress(stage, fraction):
        write_json(root / "progress.json", {"stage": stage, "fraction": fraction})
        print(stage, flush=True)

    progress("runtime", 0.02)
    archive = cache / "python-3.12.10-embed-amd64.zip"
    download(PYTHON_URL, archive, PYTHON_SHA)
    env_root = root / "ace-env"
    python = env_root / "python.exe"
    if not python.is_file():
        unpack(archive, env_root)
    # Embedded Python deliberately ignores PYTHONPATH. Add only our app package, after
    # the isolated AI dependencies; no user site packages or system Python are used.
    app_site = env_root / "app"
    shutil.copytree(
        Path(__file__).resolve().parents[1],
        app_site / "music_studio",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (env_root / "python312._pth").write_text(
        "python312.zip\n.\nLib/site-packages\n" + str(app_site) + "\nimport site\n",
        encoding="utf-8",
    )
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONHOME", "PYTHONPATH")}
    env.update(
        PYTHONUTF8="1",
        PYTHONUNBUFFERED="1",
        PIP_DISABLE_PIP_VERSION_CHECK="1",
        HF_HUB_DISABLE_TELEMETRY="1",
        DO_NOT_TRACK="1",
        GRADIO_ANALYTICS_ENABLED="False",
        HF_HUB_OFFLINE="0",
        TRANSFORMERS_OFFLINE="0",
    )
    # Pinned pip is bootstrapped as a wheel, not an unverified get-pip script.
    with urllib.request.urlopen("https://pypi.org/pypi/pip/25.2/json", timeout=30) as response:
        metadata = json.load(response)
    wheel = next(x for x in metadata["urls"] if x["filename"].endswith(".whl"))
    pip = cache / wheel["filename"]
    download(wheel["url"], pip, wheel["digests"]["sha256"])
    run(
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
    progress("dependencies", 0.08)
    wheels = [windows_wheel(name, "cp312", cache) for name in ("torch", "torchaudio")]
    run(python, "-m", "pip", "install", "--no-warn-script-location", *wheels, env=env)
    run(
        python,
        "-m",
        "pip",
        "install",
        "--no-warn-script-location",
        "--only-binary=:all:",
        "-r",
        Path(__file__).with_name("ace-requirements.txt"),
        env=env,
    )
    progress("source", 0.4)
    source = root / ("source-" + SOURCE)
    install_source(source, cache / ("source-" + SOURCE + ".zip"))
    progress("models", 0.45)
    snapshot = root / "models" / MODEL
    snapshot.mkdir(parents=True, exist_ok=True)
    # Hugging Face resumes incomplete files. Every selected file is checked against
    # the pinned repository's LFS SHA256 or Git blob hash before it becomes ready.
    downloader = r"""
import hashlib,json,sys
from pathlib import Path
from huggingface_hub import HfApi,snapshot_download
revision,folder=sys.argv[1:]
patterns=['acestep-v15-turbo/*','vae/*','Qwen3-Embedding-0.6B/*','README.md']
snapshot_download('ACE-Step/Ace-Step1.5',revision=revision,local_dir=folder,allow_patterns=patterns)
metadata=HfApi().model_info('ACE-Step/Ace-Step1.5',revision=revision,files_metadata=True)
files=[]
for item in metadata.siblings:
    path=Path(folder)/item.rfilename
    if not path.is_file():continue
    with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if item.lfs and actual!=item.lfs.sha256:raise RuntimeError('Checkpoint checksum mismatch')
    if not item.lfs and item.blob_id:
        raw=path.read_bytes()
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=item.blob_id:
            raise RuntimeError('Checkpoint metadata changed')
    files.append({'file':item.rfilename,'bytes':path.stat().st_size,'sha256':actual})
Path(folder,'music-studio-manifest.json').write_text(json.dumps({'revision':revision,'files':files},indent=2))
"""
    run(python, "-X", "utf8", "-c", downloader, MODEL, snapshot, env=env)
    view = prepare_model_view(source, snapshot)
    config = {
        "python": str(python),
        "source": str(source),
        "checkpoints": str(view),
        "download_snapshot": str(snapshot),
        "source_revision": SOURCE,
        "model_revision": MODEL,
        "source_archive_sha256": ARCHIVE_SHA256,
        "weights_manifest_sha256": digest(view / "music-studio-manifest.json"),
        "profile": "cuda-int8-offload-v3-pread",
        "quantization": "int8_weight_only",
        "managed": True,
    }
    progress("verify", 0.88)
    verification = root / "verification"
    request = root / "verification-request.json"
    write_json(
        request,
        {
            "runtime": config,
            "output": str(verification),
            "owner_pid": os.getpid(),
            "parameters": {
                "prompt": "Gentle instrumental piano and soft drums, warm melody",
                "instrumental": True,
                "duration": 12,
                "bpm": 100,
                "seed": 42,
                "steps": 8,
            },
        },
    )
    offline = {**env, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    run(python, "-X", "utf8", "-m", "music_studio.studio.ace_worker", request, env=offline)
    result = read_json(verification / "result.json")
    if not (verification / "generated.wav").is_file() or not result.get("metrics", {}).get(
        "device"
    ):
        raise RuntimeError("AI verification did not produce a CUDA audio result")
    config["verification"] = result["metrics"]
    # Publish only after a real inference succeeded. A failed/cancelled setup never
    # replaces a working runtime configuration.
    write_json(root / "acestep-runtime.json", config)
    progress("complete", 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--owner-pid", type=int)
    options = parser.parse_args()
    if options.owner_pid:
        threading.Thread(target=watch_backend, args=(options.owner_pid,), daemon=True).start()
    install(options.root.resolve())
