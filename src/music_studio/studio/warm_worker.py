"""One bounded capability process, owned by the same queue lock as generation."""

import json
import os
import subprocess
import time

from ..io import read_json
from .process import TaskStopped, stop_owned_process

REUSABLE = {"mel-band-roformer-kj", "demucs-htdemucs", "demucs-four-stems", "whisper-small"}
IDLE_SECONDS = 30


class WarmWorker:
    def __init__(self, python, environment, directory, identity):
        self.identity = identity
        self.last_used = time.monotonic()
        self.log = (directory / "worker-host.log").open("w", encoding="utf-8")
        environment = {**environment, "MUSIC_WORKBENCH_REUSE_MODEL": "1"}
        self.process = subprocess.Popen(
            [
                python,
                "-X",
                "utf8",
                "-m",
                "music_studio.studio.task_worker",
                "--serve",
                str(os.getpid()),
            ],
            stdin=subprocess.PIPE,
            stdout=self.log,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            env=environment,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            start_new_session=os.name != "nt",
        )

    def run(self, request_file, *, cancelled, timeout=7200):
        response = request_file.parent / "worker-response.json"
        started = time.monotonic()
        try:
            if cancelled():
                raise TaskStopped("Task cancelled")
            self.process.stdin.write(json.dumps(str(request_file)) + "\n")
            self.process.stdin.flush()
            while True:
                if cancelled():
                    raise TaskStopped("Task cancelled")
                if response.is_file():
                    reply = read_json(response)
                    if reply["code"]:
                        self.close()
                    self.last_used = time.monotonic()
                    return reply["code"]
                if self.process.poll() is not None:
                    raise RuntimeError(f"Capability worker exited {self.process.returncode}")
                if time.monotonic() - started > timeout:
                    raise TimeoutError(f"Local task exceeded {timeout}s")
                time.sleep(0.1)
        except BaseException:
            self.close()
            raise

    def close(self):
        stop_owned_process(self.process)
        self.process.stdin.close()
        self.log.close()
