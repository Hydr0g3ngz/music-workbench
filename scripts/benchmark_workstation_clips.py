"""Measure selected-clip tasks and model reuse against a dedicated QA server.

Creates one new QA project; does not edit existing projects or download models.
Start a server with a separate workspace before running this script. These timings
include environment checks and worker startup; they are not quality measurements.
"""

import argparse
import time
from pathlib import Path

import httpx

from music_studio.io import write_json


def main(args):
    with httpx.Client(base_url=args.url, trust_env=False, timeout=240) as client:

        def request(method, url, **kwargs):
            response = client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

        state = request(
            "POST",
            "/api/workstation/projects",
            json={
                "title": "Benchmark: selected clips · " + args.model,
            },
        )
        base = "/api/workstation/projects/" + state["id"]
        with args.audio.open("rb") as audio:
            state = request(
                "POST",
                base + "/import",
                params={"revision": 0},
                files={"file": (args.audio.name, audio)},
            )
        clip = state["content"]["tracks"][0]["clips"][0]
        if args.start + args.duration > clip["duration"]:
            raise ValueError("Requested selection exceeds the imported audio")
        clip.update(offset=args.start, duration=args.duration)
        state = request(
            "PUT", base, json={"revision": state["revision"], "content": state["content"]}
        )
        report = {
            "schema": 1,
            "project": state["id"],
            "model": args.model,
            "runs": [],
            "limits": "Single host; OS caches are not flushed. Not a quality evaluation.",
        }
        # A different capability retires any prior resident worker before the measured pair.
        for model in ["inspect"] + [args.model] * args.repeats:
            started = time.perf_counter()
            job = request(
                "POST",
                base + "/process",
                json={
                    "revision": state["revision"],
                    "clip": clip["id"],
                    "model": model,
                    "device": "cpu" if model == "inspect" else args.device,
                },
            )
            deadline = time.monotonic() + 7200
            while time.monotonic() < deadline:
                task = next(t for t in request("GET", base + "/processing") if t["id"] == job["id"])
                if task["status"] not in ("queued", "checking", "running", "cancelling"):
                    if task["status"] != "complete":
                        raise RuntimeError(task.get("error") or task["status"])
                    break
                time.sleep(0.25)
            else:
                raise TimeoutError(job["id"])
            if model == "inspect":
                continue
            report["runs"].append(
                {
                    "task": task["id"],
                    "input_sha256": task["input_sha256"],
                    "source_range": task["source_range"],
                    "input_audio": task["input_audio"],
                    "metrics": task["metrics"],
                    "observed_seconds": round(time.perf_counter() - started, 3),
                }
            )
            write_json(args.output, report)
            print(report["runs"][-1], flush=True)
        assert len({r["input_sha256"] for r in report["runs"]}) == 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--url", default="http://127.0.0.1:8933")
    parser.add_argument("--model", default="mel-band-roformer-kj")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--duration", type=float, default=12)
    parser.add_argument("--repeats", type=int, choices=range(1, 11), default=2)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args())
