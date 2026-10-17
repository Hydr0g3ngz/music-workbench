"""Run against an installed wheel without Torch models or downloaded neural weights.

Install the wheel with [ui,audio,agent] plus httpx. Assertions cover the packaged
classic and Next UI, real audio edits, the isolated local queue, exports and recovery.
"""

import argparse
import importlib.util
import io
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

import music_studio
from music_studio.io import read_json, sha256
from music_studio.ui.server import create_app


def verify(*, no_models=False):
    package = Path(music_studio.__file__).resolve().parent
    if no_models:
        for name in ("torch", "demucs", "faster_whisper", "qwen_asr"):
            assert importlib.util.find_spec(name) is None, f"Expected no {name} in preview venv"
    assert "site-packages" in package.parts, "Verify the installed wheel, not an editable checkout"
    bundled = package / "ui/demo"
    manifest = read_json(bundled / "manifest.json")
    assert all(sha256(bundled / name) == digest for name, digest in manifest["files"].items())
    with tempfile.TemporaryDirectory(prefix="music-studio-release-") as temporary:
        with TestClient(create_app(Path(temporary)), base_url="http://127.0.0.1") as client:
            assert client.get("/").status_code == 200
            for asset in ("i18n.js", "app.js", "playback.js", "style.css", "workbench.css"):
                assert client.get(f"/{asset}").status_code == 200
            system = client.get("/api/system").json()
            if no_models:
                assert not system["inference_installed"]
            job = client.post("/api/demo").json()
            assert job["has_result"] and job["status"] == "complete"
            prefix = f"/api/projects/{job['id']}"
            project = client.get(f"{prefix}/result").json()
            assert project["audio"]["duration"] == 45
            assert client.get(f"{prefix}/waveforms").json()["source"]
            for name in project["assets"]:
                assert client.get(f"{prefix}/assets/{name}").status_code == 200
            line = project["lyrics"]["segments"][0]
            response = client.patch(
                f"{prefix}/lyrics",
                json={
                    "version": "original",
                    "revision": 0,
                    "changes": {line["id"]: "Release smoke test"},
                },
            )
            assert response.status_code == 200
            assert "Release smoke test" in client.get(f"{prefix}/assets/lrc").text
            assert client.delete(prefix).status_code == 200
            assert client.get(prefix).status_code == 404
            assert client.post(f"/api/trash/{job['id']}/restore").status_code == 200
            assert (
                client.get(f"{prefix}/result").json()["lyrics"]["segments"][0]["text"]
                == "Release smoke test"
            )
            if no_models:
                error = client.post(f"{prefix}/analyze", json={})
                assert error.status_code == 503 and "setup.ps1" in error.json()["detail"]
    print(f"PASS: installed wheel {music_studio.__version__}; UI/demo/assets/edits/export/trash")
    print(f"PASS: credited demo hashes; no-model runtime={no_models}")


def verify_next():
    with tempfile.TemporaryDirectory(prefix="music-studio-next-release-") as temporary:
        with TestClient(create_app(Path(temporary)), base_url="http://127.0.0.1") as client:
            assert client.get("/next.html").status_code == 200
            for asset in (
                "station.html",
                "station-recorder.js",
                "station-recorder-worklet.js",
                "station-recording-ui.js",
                "station-recording.css",
                "station-timing.js",
                "station-timing-ui.js",
                "station-timing.css",
                "station-tutorial.js",
                "station-tutorial.css",
                "learn.html",
                "learn.js",
                "learn.css",
            ):
                assert client.get("/" + asset).status_code == 200
            for asset in ("next.js", "next.css", "transport.js", "comparison.js"):
                assert client.get("/" + asset).status_code == 200
            models = client.get("/api/studio/models").json()
            assert {"inspect", "demucs-htdemucs", "mel-band-roformer-kj"} <= {
                m["id"] for m in models
            }
            assert all(m["health"]["state"] == "unchecked" for m in models)
            speech = client.post("/api/studio/demo/speech").json()
            assert speech["attribution"]["license"] == "CC BY 4.0"
            speech_state = client.get(f"/api/projects/{speech['id']}/studio").json()
            assert abs(speech_state["audio"]["duration"] - 23.111625) < 1 / 44100
            data = io.BytesIO()
            t = np.arange(88200) / 44100
            signal = np.column_stack([np.sin(t * np.pi * 440), np.cos(t * np.pi * 660)]) * 0.2
            sf.write(data, signal, 44100, format="WAV", subtype="PCM_24")
            uploaded = client.post(
                "/api/projects", files={"file": ("Unicode-音频.wav", data.getvalue())}
            )
            assert uploaded.status_code == 201
            project = uploaded.json()["id"]
            prefix = f"/api/projects/{project}/studio"
            state = client.get(prefix).json()
            assert state["audio"]["frames"] == 88200
            preview = client.post(
                prefix + "/preview",
                json={
                    "revision": 0,
                    "operations": [
                        {"type": "trim", "start": 0.25, "end": 1.25},
                        {"type": "gain", "db": -3},
                        {"type": "fade", "in_seconds": 0.05, "out_seconds": 0.05},
                    ],
                },
            )
            assert preview.status_code == 201, preview.text
            candidate = preview.json()["id"]
            assert (
                client.post(
                    prefix + "/adopt", json={"revision": 0, "candidate": candidate}
                ).status_code
                == 200
            )
            assert (
                client.post(prefix + "/history/undo", json={"revision": 1}).json()["active"]
                == "source"
            )
            assert (
                client.post(prefix + "/history/redo", json={"revision": 2}).json()["active"]
                == "candidate:" + candidate
            )
            exported = client.post(
                prefix + "/export", json={"revision": 3, "subtype": "PCM_24"}
            ).json()
            info = sf.info(io.BytesIO(client.get(exported["url"]).content))
            assert info.frames == 44100 and info.subtype == "PCM_24"
            queued = client.post(prefix + "/tasks", json={"revision": 3, "model": "inspect"})
            assert queued.status_code == 202, queued.text
            deadline = time.monotonic() + 30
            task = queued.json()
            while time.monotonic() < deadline:
                task = client.get(prefix + "/tasks").json()[0]
                if task["status"] in ("complete", "failed", "interrupted"):
                    break
                time.sleep(0.1)
            assert task["status"] == "complete", task
            artifact = task["artifacts"][0]["id"]
            assert client.get(prefix + "/artifacts/" + artifact).json()["frames"] == 44100
            assert client.get(prefix).json()["revision"] == 3
            normalized = client.post(
                prefix + "/preview",
                json={
                    "revision": 3,
                    "operations": [{"type": "loudness", "target_lufs": -16, "ceiling_dbtp": -1}],
                },
            )
            assert normalized.status_code == 201, normalized.text
            result = normalized.json()
            assert result["processing"][0]["loudness"]["after"]["true_peak_dbtp"] <= -1
            pair = client.post(
                prefix + "/compare",
                json={"reference": "current", "processed": "candidate:" + result["id"]},
            )
            assert pair.status_code == 200, pair.text
            assert pair.json()["matching_available"]
            assert client.get(prefix).json()["revision"] == 3
            assert client.delete(f"/api/projects/{project}").status_code == 200
            assert client.post(f"/api/trash/{project}/restore").status_code == 200
    print(
        "PASS: Next installed UI/speech demo/edit/history/WAV/isolated task/assets/LUFS/A-B/trash"
    )


def verify_create():
    from music_studio.studio import library

    with tempfile.TemporaryDirectory(prefix="music-studio-create-release-") as temporary:
        with TestClient(create_app(Path(temporary)), base_url="http://127.0.0.1") as client:
            for asset in (
                "station.html",
                "station.js",
                "station-engine.js",
                "station-edit.js",
                "station-workflow.js",
                "station-workflow.css",
                "station-composition.js",
                "station-composition-ui.js",
                "station-composition.css",
                "station-fit.js",
                "station-fit-ui.js",
                "station-audition-ui.js",
                "station-material.css",
                "comparison.js",
                "station-library.css",
                "effects-dsp.js",
                "station-worklet.js",
                "station-effects.css",
            ):
                assert client.get("/" + asset).status_code == 200
            pack = client.get("/api/workstation/library").json()
            assert len(pack["samples"]) == 23 and len(pack["patterns"]) == 8
            for sample in pack["samples"]:
                data = library.sample(sample["id"])
                assert np.isfinite(data).all() and np.abs(data).max() > 0
            project = client.post(
                "/api/workstation/projects", json={"title": "Factory pack"}
            ).json()
            prefix = f"/api/workstation/projects/{project['id']}"
            state = client.post(
                prefix + "/patterns",
                json={
                    "revision": 0,
                    "pattern": pack["patterns"][0]["id"],
                },
            ).json()
            output = client.post(prefix + "/export/wav", json={"revision": state["revision"]})
            assert output.status_code == 200, output.text
            audio, rate = sf.read(io.BytesIO(client.get(output.json()["url"]).content))
            assert rate == 44100 and np.abs(audio).max() > 0.01
            assert "CC-BY-4.0" in client.get(prefix + "/credits").text
            dry_frames = len(audio)
            state["content"]["tracks"][0]["effects"] = {
                "eq": {"enabled": True, "low_db": 2},
                "compressor": {"enabled": True, "threshold_db": -24},
                "reverb": {"enabled": True, "mix": 0.25, "decay": 0.8},
            }
            state["content"]["limiter"] = {"enabled": True, "ceiling_db": -3}
            updated = client.put(
                prefix,
                json={
                    "revision": state["revision"],
                    "content": state["content"],
                },
            )
            assert updated.status_code == 200, updated.text
            state = updated.json()
            state["content"]["loop"] = {"enabled": True, "start": 2, "end": 6}
            state["content"]["metronome"] = {"enabled": True, "volume_db": -24, "accent": True}
            timing = client.put(
                prefix, json={"revision": state["revision"], "content": state["content"]}
            )
            assert timing.status_code == 200, timing.text
            state = timing.json()
            assert client.get(prefix).json()["content"]["loop"]["end"] == 6
            output = client.post(prefix + "/export/wav", json={"revision": state["revision"]})
            assert output.status_code == 200, output.text
            processed, rate = sf.read(io.BytesIO(client.get(output.json()["url"]).content))
            assert len(processed) == dry_frames + round(0.9 * rate)
            assert np.isfinite(processed).all()
            assert np.abs(processed).max() <= 10 ** (-3 / 20) + 2e-7
            undo = client.post(prefix + "/history/undo", json={"revision": state["revision"]})
            assert not undo.json()["content"]["loop"]["enabled"]
            undo = client.post(prefix + "/history/undo", json={"revision": undo.json()["revision"]})
            assert not undo.json()["content"]["limiter"]["enabled"]
            raw = io.BytesIO()
            tone = np.sin(np.arange(44100) * 2 * np.pi * 440 / 44100) * 0.1
            sf.write(raw, np.column_stack([tone, tone]), 44100, format="WAV", subtype="FLOAT")
            imported = client.post(
                prefix + f"/import?revision={undo.json()['revision']}",
                files={"file": ("fixture.wav", raw.getvalue())},
            )
            assert imported.status_code == 200, imported.text
            state = imported.json()
            clip = state["content"]["tracks"][-1]["clips"][0]
            fit = client.post(
                prefix + "/fit-preview",
                json={
                    "revision": state["revision"],
                    "clip": clip["id"],
                    "fit": {
                        "source_bpm": state["content"]["bpm"],
                        "source_anchor": 0,
                        "target_beat": 8,
                    },
                },
            )
            assert fit.status_code == 200 and fit.json()["time_ratio"] == 1
            pair = client.post(
                prefix + "/comparisons",
                json={
                    "revision": state["revision"],
                    "a": "clip:" + clip["id"],
                    "b": "clip:" + clip["id"],
                    "duration": 1,
                },
            )
            assert pair.status_code == 200, pair.text
            assert pair.json()["matching_available"]
            assert client.get(pair.json()["a"]["url"]).status_code == 200
    print(
        "PASS: Create installed UI, samples, timing, effects/history/WAV, "
        "beat fit and candidate A/B"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-models", action="store_true")
    args = parser.parse_args()
    verify(no_models=args.no_models)
    verify_next()
    verify_create()
