"""Local launch controller shared by the CLI and the Windows desktop entry point."""

import argparse
import hashlib
import json
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import urlsplit

from filelock import FileLock, Timeout
from platformdirs import user_data_path

from . import __version__
from .config import Settings
from .io import read_json, write_json


def workspace_id(workspace):
    return hashlib.sha256(os.path.normcase(str(Path(workspace).resolve())).encode()).hexdigest()


def probe(url, workspace):
    """A local identity check, without GPU inspection or system proxies."""
    if not isinstance(url, str):
        return None
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or not parsed.port
            or not 1024 <= parsed.port <= 65535
        ):
            return None
        http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with http.open(url + "/api/workstation/instance", timeout=1) as response:
            data = json.load(response)
        if data.get("product") == "music-workbench" and data.get("workspace") == workspace_id(
            workspace
        ):
            return data
    except (OSError, ValueError):
        pass
    return None


def find_instance(workspace):
    path = Path(workspace) / ".workbench-instance.json"
    try:
        data = read_json(path)
        if probe(data["url"], workspace):
            return data
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def emit(**data):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def run(workspace, settings, port=8920, open_browser=True, interface="create", controller=False):
    import uvicorn

    from .ui.server import create_app

    workspace = Path(workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(workspace / ".workbench-server.lock"), timeout=0)
    entry = {"create": "/welcome.html", "next": "/next.html"}.get(interface, "/")
    try:
        lock.acquire()
    except Timeout:
        for _ in range(40):
            existing = find_instance(workspace)
            if existing:
                url = existing["url"] + entry
                if open_browser:
                    webbrowser.open(url)
                if controller:
                    emit(
                        state="ready",
                        url=url,
                        workspace=str(workspace),
                        reused=True,
                        version=existing.get("version"),
                    )
                return existing
            time.sleep(0.25)
        raise RuntimeError(
            "The workspace is starting or busy. Please retry in a few seconds."
        ) from None
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server = None
    try:
        existing = find_instance(workspace)
        if existing:
            if open_browser:
                webbrowser.open(existing["url"] + entry)
            if controller:
                emit(
                    state="ready",
                    url=existing["url"] + entry,
                    workspace=str(workspace),
                    reused=True,
                    version=existing.get("version"),
                )
            return existing
        if not 1024 <= port <= 65535:
            raise ValueError("Port must be between 1024 and 65535")
        try:
            listener.bind(("127.0.0.1", port))
        except OSError:
            listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        url = f"http://127.0.0.1:{listener.getsockname()[1]}"
        server = uvicorn.Server(
            uvicorn.Config(
                create_app(workspace, settings),
                host="127.0.0.1",
                log_level="info",
                access_log=not controller,
            )
        )
        if controller:
            emit(state="starting", workspace=str(workspace))
        thread = threading.Thread(target=lambda: server.run(sockets=[listener]), daemon=True)
        thread.start()
        deadline = time.monotonic() + 30
        while thread.is_alive() and time.monotonic() < deadline:
            if server.started and probe(url, workspace):
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("Workbench could not start. Open the startup log for details.")
        descriptor = {
            "url": url,
            "pid": os.getpid(),
            "workspace": workspace_id(workspace),
            "version": __version__,
        }
        write_json(workspace / ".workbench-instance.json", descriptor)
        if open_browser:
            webbrowser.open(url + entry)
        if controller:
            emit(
                state="ready",
                url=url + entry,
                workspace=str(workspace),
                reused=False,
                version=__version__,
            )
            # EOF also shuts down the process owned by a closed/crashed launcher.
            for line in sys.stdin:
                if line.strip() == "quit":
                    break
            server.should_exit = True
        try:
            while thread.is_alive():
                thread.join(0.25)
        except KeyboardInterrupt:
            server.should_exit = True
            thread.join(30)
        return descriptor
    finally:
        if server:
            server.should_exit = True
        listener.close()
        lock.release()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workspace",
        type=Path,
        default=user_data_path("MusicWorkbench", appauthor=False) / "Projects",
    )
    parser.add_argument("--port", type=int, default=8920)
    parser.add_argument("--controller", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    saved = args.workspace / ".studio-runtime.json"
    settings = Settings(offline=True)
    if saved.is_file():
        values = read_json(saved)
        settings = Settings(**{k: v for k, v in values.items() if k in Settings.model_fields})
    config = Path.cwd() / ".artifacts/acestep-runtime.json"
    if config.is_file():
        os.environ.setdefault("MUSIC_STUDIO_ACE_CONFIG", str(config))
    try:
        run(args.workspace, settings, args.port, not args.no_browser, controller=args.controller)
    except Exception as error:
        if args.controller:
            emit(state="error", message=str(error))
        else:
            print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
