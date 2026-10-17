"""Smoke-test the bundled Python with only System32 on PATH; no models are required."""

import argparse
import json
import os
import queue
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path


def verify(directory, workspace):
    directory, workspace = directory.resolve(), workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    environment = {
        k: v
        for k, v in os.environ.items()
        if k not in ("PYTHONPATH", "PYTHONHOME", "MUSIC_STUDIO_ACE_CONFIG")
    }
    environment["PATH"] = str(Path(os.environ["WINDIR"]) / "System32")
    environment["PYTHONUTF8"] = "1"
    http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with (
        socket.socket() as occupied,
        (workspace / "portable-verification.log").open("w", encoding="utf-8") as log,
    ):
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        port = occupied.getsockname()[1]
        command = [
            str(directory / "runtime/python.exe"),
            "-X",
            "utf8",
            "-m",
            "music_studio.desktop",
            "--controller",
            "--no-browser",
            "--workspace",
            str(workspace),
            "--port",
            str(port),
        ]

        def start():
            process = subprocess.Popen(
                command,
                cwd=directory,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log,
                text=True,
                encoding="utf-8",
            )
            messages = queue.Queue()

            def reader():
                for line in process.stdout:
                    messages.put(line)
                messages.put(None)

            threading.Thread(target=reader, daemon=True).start()
            deadline = time.monotonic() + 35
            try:
                while time.monotonic() < deadline:
                    line = messages.get(timeout=max(0.1, deadline - time.monotonic()))
                    if line is None:
                        raise RuntimeError("Portable startup exited; inspect the verification log")
                    try:
                        data = json.loads(line)
                    except ValueError:
                        log.write(line)
                        continue
                    if data["state"] == "error":
                        raise RuntimeError(data["message"])
                    if data["state"] == "ready":
                        return process, data
                raise RuntimeError("Portable startup timed out")
            except Exception:
                process.stdin.close()
                process.wait(40)
                raise

        process, ready = start()
        try:
            assert not ready["reused"], "Use a workspace without an existing server"
            base = ready["url"].removesuffix("/welcome.html")
            assert int(base.rsplit(":", 1)[1]) != port
            second, reused = start()
            second.wait(5)
            assert reused["reused"] and reused["url"] == ready["url"]

            def request(path, data=None):
                req = urllib.request.Request(
                    base + path,
                    data=json.dumps(data).encode() if data is not None else None,
                    headers={"Content-Type": "application/json"},
                )
                with http.open(req, timeout=60) as response:
                    return json.load(response)

            project = request("/api/workstation/projects", {"demo": True})
            assert len(project["content"]["tracks"]) == 4
            prefix = "/api/workstation/projects/" + project["id"]
            exported = request(prefix + "/export/wav", {"revision": project["revision"]})
            with http.open(base + exported["url"], timeout=60) as response:
                assert response.read(4) == b"RIFF"
            assert not request("/api/workstation/generation/status")["available"]
            result = {
                "version": ready["version"],
                "system_python_not_used": True,
                "port_conflict_recovered": True,
                "relaunch_reused": True,
                "no_models_basic_creation": True,
                "example_wav_exported": True,
            }
            (workspace / "portable-verification.json").write_text(
                json.dumps(result, indent=2), encoding="utf-8"
            )
            return result
        finally:
            if process.poll() is None:
                process.stdin.write("quit\n")
                process.stdin.flush()
                process.wait(40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.directory, args.workspace)))
