"""Portable projects: canonical audio + checked manifest, never executable model files."""

import hashlib
import io
import json
import re
import zipfile

import soundfile as sf

from ..io import sha256
from . import dsp
from .arrangement import RATE, Arrangement, uid
from .service import StudioError

LIMIT = 512 * 1024**2


def export_pack(service, key, revision):
    state = service.get(key)
    if state["revision"] != revision:
        raise StudioError("Session changed; save before packaging", 409)
    root = service.studio.root / ".arrangement-exports"
    if root.is_symlink():
        raise StudioError("Invalid export directory")
    root.mkdir(exist_ok=True)
    target = root / (uid() + ".mwb")
    manifest = {
        "format": "music-workbench-pack",
        "version": 1,
        "content": state["content"],
        "assets": [],
    }
    total = 0
    try:
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as archive:
            for asset in state["assets"]:
                path = service.asset_path(key, asset["id"])
                total += path.stat().st_size
                if total > LIMIT:
                    raise StudioError("Portable project limit is 512 MiB")
                filename = f"assets/{asset['id']}.wav"
                archive.write(path, filename)
                manifest["assets"].append(
                    {
                        "id": asset["id"],
                        "name": asset["name"],
                        "file": filename,
                        "sha256": sha256(path),
                    }
                )
            archive.writestr("project.json", json.dumps(manifest, ensure_ascii=False))
            archive.writestr("credits.txt", service.credits(key))
        return {
            "url": "/api/workstation/exports/" + target.name,
            "revision": revision,
            "kind": "mwb",
            "name": state["content"]["title"],
        }
    except Exception:
        target.unlink(missing_ok=True)
        raise


def restore_pack(service, upload):
    upload.file.seek(0, 2)
    if upload.file.tell() > LIMIT + 8 * 1024**2:
        raise StudioError("Portable project upload limit is 512 MiB", 413)
    upload.file.seek(0)
    try:
        with zipfile.ZipFile(upload.file) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if (
                len(entries) > 258
                or len(set(names)) != len(names)
                or sum(entry.file_size for entry in entries) > LIMIT + 4 * 1024**2
                or any(entry.flag_bits & 1 for entry in entries)
            ):
                raise ValueError("Invalid archive limits or duplicate entries")
            if archive.getinfo("project.json").file_size > 4 * 1024**2:
                raise ValueError("Project manifest is too large")
            manifest = json.loads(archive.read("project.json"))
            if manifest.get("format") != "music-workbench-pack" or manifest.get("version") != 1:
                raise ValueError("Unsupported project pack")
            content = Arrangement.model_validate(manifest["content"])
            assets = manifest["assets"]
            if not isinstance(assets, list) or len(assets) > 256:
                raise ValueError("Invalid assets")
            checked, ids = [], set()
            # Validate every path, checksum, audio header and clip bound before creating a project.
            for asset in assets:
                identity, filename = asset["id"], asset["file"]
                if (
                    not re.fullmatch(r"[a-f0-9]{16}", identity)
                    or identity in ids
                    or filename != f"assets/{identity}.wav"
                    or not isinstance(asset["name"], str)
                    or not 1 <= len(asset["name"]) <= 500
                    or archive.getinfo(filename).file_size > 256 * 1024**2
                ):
                    raise ValueError("Invalid asset metadata")
                ids.add(identity)
                raw = archive.read(filename)
                if hashlib.sha256(raw).hexdigest() != asset["sha256"]:
                    raise ValueError("Asset checksum mismatch")
                info = sf.info(io.BytesIO(raw))
                if info.samplerate != RATE or info.channels != 2 or not 0 < info.duration <= 600:
                    raise ValueError("Unsupported project audio")
                checked.append({"id": identity, "name": asset["name"], "duration": info.duration})
            allowed = {"project.json", "credits.txt", *(a["file"] for a in assets)}
            if set(names) - allowed:
                raise ValueError("Unexpected archive entries")
            service.validate(content, checked)
            for asset, record in zip(assets, checked, strict=True):
                with archive.open(asset["file"]) as stream:
                    source = service.import_stream(asset["name"] + ".wav", stream)
                path = service.studio.asset_path(source["id"], "source")
                record.update(
                    source_project=source["id"],
                    source_asset="source",
                    waveform=dsp.peaks(path, 480),
                )
            # Insert the complete restored project atomically, with fresh history and identity.
            import time

            now, key = time.time(), uid()
            with service.studio.transaction() as db:
                db.execute(
                    "INSERT INTO arrangements VALUES (?,?,?,?,?,?,?,?,0)",
                    (key, 0, content.model_dump_json(), json.dumps(checked), "[]", "[]", now, now),
                )
            return service.get(key)
    except (
        ValueError,
        KeyError,
        TypeError,
        zipfile.BadZipFile,
        RuntimeError,
        sf.LibsndfileError,
    ) as e:
        raise StudioError("Cannot restore project pack: " + str(e)) from e
