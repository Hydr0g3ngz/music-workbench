from __future__ import annotations

import contextlib
import importlib.util
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .. import __version__
from ..config import Settings
from ..export import export_project
from ..io import fingerprint, read_json, sha256, write_json
from ..pipeline import AnalysisCancelled, analyze
from ..review import line_identity, review_summary
from ..schema import Project
from ..studio.models import WeightInstallRequest
from .revisions import (
    edited_project,
    edits_path,
    edits_state,
    result_folder,
    update_lyrics,
    versions,
)
from .runtime import runtime_capabilities, runtime_error

DEMO = {
    "title": "Let's Go Fishin'",
    "artist": "Karissa Hobbs",
    "license": "CC BY 3.0",
    "license_url": "https://creativecommons.org/licenses/by/3.0/",
    "source_url": "https://librosa.org/data/audio/Karissa_Hobbs_-_Lets_Go_Fishin.txt",
}
STAGES = ["decode", "separate", "lyrics", "melody", "rhythm", "harmony"]
LABELS = {
    "decode": "准备音频",
    "separate": "分离人声与伴奏",
    "lyrics": "识别歌词",
    "melody": "提取主旋律",
    "rhythm": "检测节拍",
    "harmony": "分析和弦",
}
EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aac", ".opus", ".aiff"}


class StartOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device: str = "auto"
    language: str | None = None
    offline: bool = False
    quality: Literal["configured", "balanced", "text", "qwen", "heart"] = "configured"
    scope: Literal["full", "lyrics", "align", "reference", "retry"] = "full"
    alignment: Literal["native", "qwen", "whisper", "anchors", "anchors_dual"] = "native"
    lyrics_input: Literal["vocals", "source"] = "vocals"
    base_version: str | None = None
    edit_revision: int | None = Field(default=None, ge=0)
    reference_text: str | None = Field(default=None, max_length=50000)
    line_id: str | None = Field(default=None, max_length=80)
    candidate: bool = False


class VersionSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    expected_current: str


class RenameOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=150)


class LyricsPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=0)
    changes: dict[str, str | None] = Field(min_length=1, max_length=200)
    version: str = "original"


class ReviewPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    revision: int = Field(ge=0)
    line_id: str
    reviewed: bool = True


def waveform(path: Path, bins: int = 1800) -> list[float]:
    """Real peak envelope, not decorative waveform data. Bounded memory reads."""
    with sf.SoundFile(path) as audio:
        step = max(1, int(np.ceil(len(audio) / bins)))
        result = []
        for data in audio.blocks(blocksize=step, dtype="float32", always_2d=True):
            result.append(round(float(np.max(np.abs(data))), 5))
    return result


class JobManager:
    def __init__(self, workspace: Path, settings: Settings, analyzer=analyze):
        self.root = workspace.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.settings = settings.resolved()
        self.analyzer = analyzer
        self.lock = threading.RLock()
        self.thread: threading.Thread | None = None
        self.active_id: str | None = None
        self.cancel_event = threading.Event()
        self.closing = False
        # Workers are owned by this process. An earlier stopped server cannot report live work.
        for entry in self.root.glob("*/job.json"):
            with contextlib.suppress(ValueError, OSError):
                record = read_json(entry)
                if record.get("status") in ("running", "cancelling"):
                    record.update(status="interrupted", error="上次分析已中断，可以继续分析。")
                    pending = record.pop("pending_version", None)
                    if pending and re.fullmatch(r"[a-f0-9]{16}", pending):
                        metadata = entry.parent / "revisions" / f"{pending}.json"
                        if metadata.is_file():
                            state = read_json(metadata)
                            state.update(status="interrupted", error=record["error"])
                            write_json(metadata, state)
                    write_json(entry, record)

    def directory(self, project_id: str, *, trashed: bool = False) -> Path:
        if not re.fullmatch(r"[a-f0-9]{16}", project_id):
            raise HTTPException(404, "项目不存在")
        parent = self.root / ".trash" if trashed else self.root
        if parent.is_symlink() or not parent.resolve().is_relative_to(self.root):
            raise HTTPException(404, "项目不存在")
        candidate = parent / project_id
        path = candidate.resolve()
        if (
            candidate.is_symlink()
            or path.parent != parent.resolve()
            or not (path / "job.json").is_file()
        ):
            raise HTTPException(404, "项目不存在")
        return path

    def record(self, project_id: str) -> dict:
        directory = self.directory(project_id)
        record = read_json(directory / "job.json")
        metadata = directory / ".studio/source.json"
        if record.get("duration") is None and metadata.is_file():
            with contextlib.suppress(ValueError, OSError, KeyError):
                audio_path = (directory / read_json(metadata)["file"]).resolve()
                if audio_path.is_relative_to(directory) and audio_path.is_file():
                    record["duration"] = sf.info(audio_path).duration
        record["current_version"] = record.get("current_version", "original")
        selected = result_folder(directory, record["current_version"])
        record["has_result"] = (selected / "project.json").is_file()
        pending = record.get("pending_version")
        result = result_folder(directory, pending) if pending else directory / "result"
        run = read_json(result / "run.json") if (result / "run.json").exists() else {}
        record["completed_stages"] = len(run.get("stages", {}))
        record["total_stages"] = 1 if pending and record.get("scope") != "full" else len(STAGES)
        record["stage"] = run.get("active_stage")
        record["stage_label"] = LABELS.get(record["stage"], "准备分析")
        if record["status"] in ("running", "cancelling"):
            record["elapsed_seconds"] = max(0, time.time() - record.get("started_at", time.time()))
            detail = result / "analysis/progress.json"
            if detail.is_file() and record["stage"] == "lyrics":
                with contextlib.suppress(ValueError, OSError):
                    item = read_json(detail)
                    if item["updated_at"] >= record.get("started_at", 0):
                        record["progress_detail"] = item
        if record["status"] == "complete":
            record["completed_stages"] = record["total_stages"]
        return record

    def list(self) -> list[dict]:
        records = []
        for path in self.root.glob("*/job.json"):
            with contextlib.suppress(ValueError, OSError, HTTPException):
                records.append(self.record(path.parent.name))
        return sorted(records, key=lambda x: x["created_at"], reverse=True)

    def rename(self, project_id: str, title: str):
        title = title.strip()
        if not title or any(ord(c) < 32 for c in title):
            raise HTTPException(422, "歌曲名称不能为空，也不能包含换行或控制字符")
        with self.lock:
            path = self.directory(project_id) / "job.json"
            record = read_json(path)
            record["title"] = title
            write_json(path, record)
        return self.record(project_id)

    def trash(self, project_id: str):
        with self.lock:
            if self.active_id == project_id:
                raise HTTPException(409, "请先停止当前分析，再删除歌曲")
            source = self.directory(project_id)
            target = self.root / ".trash" / project_id
            if target.parent.is_symlink() or not target.parent.resolve().is_relative_to(self.root):
                raise HTTPException(409, "回收站路径无效")
            target.parent.mkdir(exist_ok=True)
            if target.exists() or target.resolve().parent != (self.root / ".trash").resolve():
                raise HTTPException(409, "回收站中已有相同项目")
            record = read_json(source / "job.json")
            record["deleted_at"] = time.time()
            write_json(source / "job.json", record)
            source.rename(target)
            return {"id": project_id, "title": record["title"], "status": "trashed"}

    def restore(self, project_id: str):
        with self.lock:
            source = self.directory(project_id, trashed=True)
            target = self.root / project_id
            if target.exists() or target.resolve().parent != self.root:
                raise HTTPException(409, "工作区已有相同项目")
            source.rename(target)
            record = read_json(target / "job.json")
            record.pop("deleted_at", None)
            write_json(target / "job.json", record)
            return self.record(project_id)

    def trash_list(self):
        rows = []
        for entry in (self.root / ".trash").glob("*/job.json"):
            with contextlib.suppress(ValueError, OSError, HTTPException):
                path = self.directory(entry.parent.name, trashed=True)
                rows.append(read_json(path / "job.json"))
        return sorted(rows, key=lambda r: r.get("deleted_at", 0), reverse=True)

    def create(self, filename: str, source=None, attribution=None) -> tuple[dict, Path]:
        extension = Path(filename).suffix.lower()
        if extension not in EXTENSIONS:
            raise HTTPException(400, "请选择 WAV、MP3、FLAC、M4A 或 OGG 等音频文件")
        project_id = uuid.uuid4().hex[:16]
        directory = self.root / project_id
        (directory / "input").mkdir(parents=True)
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", Path(filename).name)[:150]
        destination = directory / "input" / safe_name
        record = {
            "id": project_id,
            "title": Path(safe_name).stem,
            "filename": safe_name,
            "status": "ready",
            "created_at": time.time(),
            "error": None,
            "duration": None,
            "attribution": attribution,
        }
        if source is not None:
            shutil.copyfile(source, destination)
        write_json(directory / "job.json", record)
        return record, destination

    def start(self, project_id: str, options: StartOptions) -> dict:
        with self.lock:
            if self.closing:
                raise HTTPException(503, "服务正在关闭")
            if self.active_id is not None:
                raise HTTPException(409, "已有歌曲正在分析，请完成或停止后再试")
            if self.analyzer is analyze and not all(
                importlib.util.find_spec(name) for name in ("torch", "demucs", "faster_whisper")
            ):
                raise HTTPException(
                    503, "未安装推理依赖，请先运行 scripts/setup.ps1 -Mode full，或参阅 README。"
                )
            directory = self.directory(project_id)
            record = self.record(project_id)
            selected = record["current_version"]
            if options.base_version is not None and options.base_version != selected:
                raise HTTPException(409, "当前分析版本已切换，请刷新后再试")
            base = result_folder(directory, selected) if record["has_result"] else None
            if options.scope != "full" and base is None:
                raise HTTPException(409, "请先完成整曲分析，再更新歌词")
            if options.candidate and options.scope != "retry":
                raise HTTPException(422, "识别候选只适用于单句重识别")
            supplied = None
            if options.scope in ("align", "reference", "retry"):
                if options.base_version is None:
                    raise HTTPException(422, "对齐任务必须指定歌词所属的版本")
                state = edits_state(base)
                if options.edit_revision != state["revision"]:
                    raise HTTPException(409, "歌词已更新，请刷新后再对齐")
                from ..backends.lyric_alignment import language_name, reference_lyrics

                project = edited_project(
                    base, Project.model_validate(read_json(base / "project.json"))
                )
                try:
                    if options.scope != "retry":
                        language_name(options.language or project.lyrics.language)
                    if options.scope == "retry" and options.line_id not in {
                        line.id for line in project.lyrics.segments
                    }:
                        raise ValueError("要重新识别的歌词句不存在")
                    supplied = (
                        reference_lyrics(
                            options.reference_text or "", project.lyrics, project.audio.duration
                        )
                        if options.scope == "reference"
                        else project.lyrics
                    )
                except ValueError as error:
                    raise HTTPException(422, str(error)) from error
            try:
                model = {"text": "large-v3-turbo", "balanced": "small"}.get(
                    options.quality, self.settings.asr_model
                )
                from ..lyric_models import MODELS

                backend = options.quality if options.quality in ("qwen", "heart") else "whisper"
                revision = self.settings.asr_revision if model == self.settings.asr_model else None
                if backend != "whisper":
                    model, revision = MODELS[backend]
                alignment = "anchors" if options.alignment == "anchors_dual" else options.alignment
                settings = Settings(
                    **{
                        **self.settings.model_dump(),
                        "device": options.device,
                        "language": options.language or None,
                        "offline": options.offline,
                        "asr_model": model,
                        "asr_revision": revision,
                        "asr_backend": backend
                        if options.quality != "configured"
                        else self.settings.asr_backend,
                        "lyrics_input": options.lyrics_input,
                        "anchor_model": "dual" if options.alignment == "anchors_dual" else "small",
                        "lyrics_alignment": (alignment if alignment != "native" else "anchors")
                        if options.scope in ("align", "reference")
                        else alignment,
                    }
                ).resolved()
            except ValueError as error:
                raise HTTPException(422, str(error)) from error
            # Reject unavailable recognizers before separation, revision creation or job writes.
            if self.analyzer is analyze:
                problem = runtime_error(settings.model_dump(), options.scope)
                if problem:
                    raise HTTPException(503, problem)
            version = uuid.uuid4().hex[:16] if base else None
            result = result_folder(directory, version) if version else directory / "result"
            if version:
                result.mkdir(parents=True)
                write_json(
                    result.with_suffix(".json"),
                    {
                        "id": version,
                        "base_version": selected,
                        "created_at": time.time(),
                        "scope": options.scope,
                        "status": "running",
                        "settings": settings.model_dump(),
                        "base_edit_revision": edits_state(base)["revision"],
                        "candidate": options.candidate,
                        "line_id": options.line_id,
                    },
                )
                record["pending_version"] = version
            record.update(
                status="running",
                error=None,
                settings=settings.model_dump(),
                scope=options.scope,
                completed_stages=0,
                total_stages=6 if options.scope == "full" else 1,
                stage=None,
                stage_label="准备分析",
                started_at=time.time(),
            )
            record.pop("candidate_version", None)
            write_json(directory / "job.json", record)
            self.active_id = project_id
            self.cancel_event = threading.Event()
            self.thread = threading.Thread(
                target=self._run,
                args=(
                    project_id,
                    settings,
                    self.cancel_event,
                    result,
                    base,
                    version,
                    supplied,
                    options.scope,
                    options.line_id,
                    options.candidate,
                ),
                daemon=True,
                name=f"music-analysis-{project_id}",
            )
            self.thread.start()
            return record

    def _run(
        self,
        project_id: str,
        settings: Settings,
        cancellation: threading.Event,
        result: Path,
        base: Path | None,
        version: str | None,
        supplied,
        scope: str,
        line_id: str | None,
        candidate: bool = False,
    ):
        directory = self.directory(project_id)
        record = read_json(directory / "job.json")
        started = time.perf_counter()
        try:
            with (directory / "progress.log").open("a", encoding="utf-8") as log:

                def progress(message):
                    log.write(message + "\n")
                    log.flush()

                if scope == "full":
                    project = self.analyzer(
                        directory / "input" / record["filename"],
                        result,
                        settings,
                        resume=(result / "run.json").exists(),
                        progress=progress,
                        cancel_event=cancellation,
                    )
                else:
                    project = update_lyrics(
                        base,
                        result,
                        settings,
                        supplied=supplied,
                        reference=scope == "reference",
                        retry_line=line_id if scope == "retry" else None,
                        progress=progress,
                        cancel_event=cancellation,
                    )
            record.update(status="complete", duration=project.audio.duration, error=None)
            record.pop("precomputed_demo", None)
            if version and not candidate:
                record["current_version"] = version
            elif version:
                record["candidate_version"] = version
        except AnalysisCancelled:
            record.update(status="cancelled", error=None)
        except Exception as error:
            record.update(status="failed", error=str(error))
        finally:
            record["elapsed_seconds"] = round(time.perf_counter() - started, 2)
            record.pop("pending_version", None)
            if version:
                metadata = read_json(result.with_suffix(".json"))
                metadata.update(
                    status=record["status"],
                    error=record["error"],
                    elapsed_seconds=record["elapsed_seconds"],
                )
                if record["status"] == "complete":
                    metadata.update(
                        settings=project.settings,
                        timing_method=project.lyrics.timing_method,
                        lyrics_count=len(project.lyrics.segments),
                    )
                write_json(result.with_suffix(".json"), metadata)
            with self.lock:
                # Renaming while a worker runs must survive its final status update.
                record["title"] = read_json(directory / "job.json")["title"]
                write_json(directory / "job.json", record)
                self.active_id = None

    def cancel(self, project_id: str):
        with self.lock:
            if self.active_id != project_id:
                raise HTTPException(409, "此项目当前没有运行中的分析")
            self.cancel_event.set()
            directory = self.directory(project_id)
            record = read_json(directory / "job.json")
            record["status"] = "cancelling"
            write_json(directory / "job.json", record)
        return {"status": "cancelling"}

    def close(self):
        with self.lock:
            self.closing = True
            self.cancel_event.set()
            thread = self.thread
        if thread is not None:
            thread.join(timeout=15)


def create_app(workspace: Path, settings: Settings | None = None, *, analyzer=analyze) -> FastAPI:
    manager = JobManager(workspace, settings or Settings(), analyzer=analyzer)
    from ..studio.ai_setup import AISetup
    from ..studio.ai_setup import router as ai_setup_router
    from ..studio.arrangement import router as arrangement_router
    from ..studio.codex import CodexBridge
    from ..studio.codex import router as codex_router
    from ..studio.http import router as studio_router
    from ..studio.model_setup import ModelSetup
    from ..studio.model_setup import router as model_setup_router
    from ..studio.service import StudioError, StudioService

    studio = StudioService(workspace, manager.settings)
    codex = CodexBridge(studio)
    ai_setup = AISetup()
    model_setup = ModelSetup(studio.tasks.registry)

    @asynccontextmanager
    async def lifespan(app):
        studio.tasks.wake.set()
        try:
            yield
        finally:
            manager.close()
            ai_setup.close()
            model_setup.close()
            codex.shutdown()
            studio.close()

    app = FastAPI(title="Music Studio", lifespan=lifespan, docs_url=None, redoc_url=None)

    @app.exception_handler(StudioError)
    async def studio_error(request, error):
        return JSONResponse({"detail": str(error)}, status_code=error.status)

    app.state.manager = manager
    app.state.studio = studio
    @app.get("/api/workstation/instance")
    def instance():
        from ..desktop import workspace_id

        return {"product": "music-workbench", "version": __version__,
                "workspace": workspace_id(workspace), "ready": True}

    app.include_router(studio_router(studio))
    app.include_router(arrangement_router(studio, manager))
    app.include_router(codex_router(codex))
    app.include_router(ai_setup_router(ai_setup))
    app.include_router(model_setup_router(model_setup))
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "[::1]"])

    @app.get("/api/studio/models")
    def local_models():
        return studio.tasks.registry.list()

    @app.post("/api/studio/models/{model}/check")
    def check_local_model(model: str):
        return studio.tasks.registry.check(model)

    @app.post("/api/studio/models/{model}/install")
    def install_local_weights(model: str, request: WeightInstallRequest | None = None):
        from ..studio.service import StudioError

        try:
            return studio.tasks.registry.install_weights(model)
        except StudioError as error:
            raise HTTPException(error.status, str(error)) from error
        except (OSError, ValueError) as error:
            raise HTTPException(422, str(error)) from error

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and origin != str(request.base_url).rstrip("/"):
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "仅接受本地界面的请求"}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/system")
    def system():
        gpu = None
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            probe = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
                creationflags=flags,
            )
            gpu = probe.stdout.strip().splitlines()[0]
        except (OSError, subprocess.SubprocessError, IndexError):
            pass
        return {
            "version": __version__,
            "gpu": gpu,
            "inference_installed": all(
                importlib.util.find_spec(name) for name in ("torch", "demucs", "faster_whisper")
            ),
            "recognizers": runtime_capabilities(manager.settings.model_dump()),
            "features": {
                "lyrics_revision": "v3-verified",
                "workbench": "v4",
                "audio_studio": "v2-cleanup",
                "speech_cleanup": True,
                "loudness": True,
                "comparison": True,
                "arrangement": "v1-preview",
                "agent_tools": "mcp+codex-experimental",
            },
            "defaults": {
                "device": manager.settings.device,
                "language": manager.settings.language,
                "offline": manager.settings.offline,
                "asr_model": manager.settings.asr_model,
                "asr_backend": manager.settings.asr_backend,
                "lyrics_alignment": manager.settings.lyrics_alignment,
                "anchor_model": manager.settings.anchor_model,
                "lyrics_input": manager.settings.lyrics_input,
            },
        }

    @app.get("/api/projects")
    def projects():
        return manager.list()

    @app.get("/api/trash")
    def trash_list():
        return manager.trash_list()

    @app.post("/api/trash/{project_id}/restore")
    def restore(project_id: str):
        return manager.restore(project_id)

    @app.post("/api/projects", status_code=201)
    async def upload(file: UploadFile):
        filename = file.filename or "audio.wav"
        record, destination = manager.create(filename)
        count = 0
        try:
            with destination.open("wb") as output:
                while block := await file.read(1024 * 1024):
                    count += len(block)
                    if count > 512 * 1024 * 1024:
                        raise HTTPException(413, "单个音频文件最大 512MB")
                    output.write(block)
            if count == 0:
                raise HTTPException(400, "音频文件为空")
        except Exception:
            # Keep a failed record visible instead of leaving a ready but incomplete upload.
            record.update(status="failed", error="文件导入失败，请重新选择音频")
            write_json(destination.parent.parent / "job.json", record)
            raise
        finally:
            await file.close()
        return record

    @app.post("/api/demo", status_code=201)
    def demo():
        bundled = Path(__file__).parent / "demo"
        manifest = read_json(bundled / "manifest.json")
        # Verify the packaged data before copying it into a writable project.
        for relative, digest in manifest["files"].items():
            source = (bundled / relative).resolve()
            if not source.is_relative_to(bundled.resolve()) or sha256(source) != digest:
                raise HTTPException(
                    503, "Bundled demo integrity check failed; reinstall Music Studio"
                )
        with manager.lock:
            record, _ = manager.create(
                "Lets-Go-Fishin-preview.ogg",
                source=bundled / "audio/source.ogg",
                attribution=manifest["attribution"],
            )
            result = manager.directory(record["id"]) / "result"
            shutil.copytree(bundled, result)
            project = Project.model_validate(read_json(result / "project.json"))
            # Lyric workers and inherited music caches use canonical float WAV.
            # Decode the compressed preview without PyAV or neural models. Retain
            # the bundle manifest as provenance for the unmodified package data.
            (result / "manifest.json").rename(result / "bundled-manifest.json")
            for name in ("source", "vocals", "instrumental"):
                decoded = f"audio/{name}.wav"
                with sf.SoundFile(result / project.assets[name]) as source:
                    if (
                        source.samplerate != project.audio.sample_rate
                        or source.channels != project.audio.channels
                        or len(source) != project.audio.samples
                    ):
                        raise HTTPException(503, "Bundled demo audio metadata is inconsistent")
                    with sf.SoundFile(
                        result / decoded,
                        "w",
                        samplerate=source.samplerate,
                        channels=source.channels,
                        subtype="FLOAT",
                    ) as output:
                        for block in source.blocks(blocksize=65536, dtype="float32"):
                            output.write(block)
                project.assets[name] = decoded
            project.warnings.append(
                "Workspace stems are float WAV decoded from the compressed demo previews. "
                "This conversion does not restore lossless original audio."
            )
            write_json(result / "project.json", project.model_dump())
            record.update(
                title="Let's Go Fishin' · Demo",
                status="complete",
                duration=project.audio.duration,
                settings=project.settings,
                precomputed_demo=True,
            )
            write_json(result.parent / "job.json", record)
            return manager.record(record["id"])

    @app.post("/api/studio/demo/speech", status_code=201)
    def speech_demo():
        bundled = Path(__file__).parent / "speech_demo"
        manifest = read_json(bundled / "manifest.json")
        source = bundled / "noisy.flac"
        if sha256(source) != manifest["files"]["noisy.flac"]:
            raise HTTPException(503, "Bundled speech example failed its integrity check")
        with manager.lock:
            record, _ = manager.create(
                "Speech-cleanup-demo.flac", source=source, attribution=manifest["attribution"]
            )
            record.update(title="Speech cleanup · Demo", demo_key="speech-v1")
            write_json(manager.directory(record["id"]) / "job.json", record)
        return manager.record(record["id"])

    @app.get("/api/projects/{project_id}")
    def project_status(project_id: str):
        return manager.record(project_id)

    @app.patch("/api/projects/{project_id}")
    def rename(project_id: str, options: RenameOptions):
        return manager.rename(project_id, options.title)

    @app.delete("/api/projects/{project_id}")
    def delete(project_id: str):
        with studio.project_guard(project_id):
            if studio.tasks.busy(project_id):
                raise HTTPException(
                    409,
                    "请先完成或取消这个项目的工作台任务 / Finish or cancel its local tasks first",
                )
            return manager.trash(project_id)

    @app.post("/api/projects/{project_id}/analyze", status_code=202)
    def start(project_id: str, options: StartOptions):
        return manager.start(project_id, options)

    @app.post("/api/projects/{project_id}/cancel")
    def cancel(project_id: str):
        return manager.cancel(project_id)

    def completed(project_id: str, version: str | None = None) -> tuple[Path, Project]:
        directory = manager.directory(project_id)
        selected = version or manager.record(project_id)["current_version"]
        result = result_folder(directory, selected)
        if not (result / "project.json").is_file():
            raise HTTPException(409, "分析完成后可查看结果")
        return result, Project.model_validate(read_json(result / "project.json"))

    @app.get("/api/projects/{project_id}/versions")
    def history(project_id: str):
        with manager.lock:
            record = manager.record(project_id)
            return {
                "current": record["current_version"],
                "versions": versions(manager.directory(project_id), record),
            }

    @app.post("/api/projects/{project_id}/versions/select")
    def select_version(project_id: str, selection: VersionSelection):
        with manager.lock:
            if manager.active_id == project_id:
                raise HTTPException(409, "请等待分析完成或先停止，再切换版本")
            record = manager.record(project_id)
            if record["current_version"] != selection.expected_current:
                raise HTTPException(409, "版本已在其他窗口切换，请刷新后再试")
            folder, project = completed(project_id, selection.version)
            metadata_path = folder.with_suffix(".json")
            if selection.version != "original" and metadata_path.is_file():
                metadata = read_json(metadata_path)
                if metadata.get("candidate"):
                    base = result_folder(manager.directory(project_id), metadata["base_version"])
                    if (
                        metadata["base_version"] != record["current_version"]
                        or edits_state(base)["revision"] != metadata["base_edit_revision"]
                    ):
                        raise HTTPException(
                            409, "原歌词或版本已改变，请重新生成候选，避免覆盖新修改"
                        )
                    metadata.update(candidate=False, accepted_at=time.time())
                    write_json(metadata_path, metadata)
            record.update(
                current_version=selection.version,
                status="complete",
                error=None,
                settings=project.settings,
            )
            record.pop("candidate_version", None)
            write_json(manager.directory(project_id) / "job.json", record)
            return manager.record(project_id)

    @app.get("/api/projects/{project_id}/compare")
    def compare_versions(project_id: str, left: str, right: str):
        from difflib import SequenceMatcher

        with manager.lock:
            sides = []
            for version in (left, right):
                folder, project = completed(project_id, version)
                project = edited_project(folder, project)
                sides.append(
                    {
                        "version": version,
                        "settings": project.settings,
                        "timing_method": project.lyrics.timing_method,
                        "segments": [line.model_dump() for line in project.lyrics.segments],
                    }
                )
            before, after = [[line["text"] for line in side["segments"]] for side in sides]
            changes = [
                {"operation": op, "left": [a, b], "right": [c, d]}
                for op, a, b, c, d in SequenceMatcher(
                    None, before, after, autojunk=False
                ).get_opcodes()
                if op != "equal"
            ]
            return {
                "left": sides[0],
                "right": sides[1],
                "changes": changes,
                "note": "文字变化不等于准确率提升；请通过试听核对。手动修改按版本保留。",
            }

    @app.get("/api/projects/{project_id}/result")
    def result(project_id: str, version: str | None = None):
        folder, project = completed(project_id, version)
        return edited_project(folder, project).model_dump()

    @app.get("/api/projects/{project_id}/lyrics")
    def lyrics(project_id: str, version: str | None = None):
        folder, project = completed(project_id, version)
        edits = edits_state(folder)
        return {
            **edits,
            "version": "original" if folder.name == "result" else folder.name,
            "original": {s.id: s.text for s in project.lyrics.segments},
            "review": review_summary(
                edited_project(folder, project).lyrics, edits.get("reviewed"), edits["changes"]
            ),
        }

    @app.patch("/api/projects/{project_id}/review")
    def patch_review(project_id: str, patch: ReviewPatch):
        with manager.lock:
            if patch.version != manager.record(project_id)["current_version"]:
                raise HTTPException(409, "当前版本已改变，请重新打开歌词后核对")
            folder, project = completed(project_id, patch.version)
            state = edits_state(folder)
            if patch.revision != state["revision"]:
                raise HTTPException(409, "歌词已在其他窗口更新，请刷新后核对")
            selected = edited_project(folder, project)
            line = next((s for s in selected.lyrics.segments if s.id == patch.line_id), None)
            if line is None:
                raise HTTPException(422, "歌词句不存在")
            state.setdefault("reviewed", {})
            if patch.reviewed:
                state["reviewed"][line.id] = line_identity(line)
            else:
                state["reviewed"].pop(line.id, None)
            state["revision"] += 1
            write_json(edits_path(folder), state)
            return {
                **state,
                "review": review_summary(selected.lyrics, state["reviewed"], state["changes"]),
            }

    @app.patch("/api/projects/{project_id}/lyrics")
    def patch_lyrics(project_id: str, patch: LyricsPatch):
        with manager.lock:
            if patch.version != manager.record(project_id)["current_version"]:
                raise HTTPException(409, "当前版本已改变，修改未写入其他版本，请重新打开歌词编辑")
            folder, project = completed(project_id, patch.version)
            state = edits_state(folder)
            if patch.revision != state["revision"]:
                raise HTTPException(409, "歌词已在其他窗口更新，请重新打开后再编辑")
            original = {s.id: s.text for s in project.lyrics.segments}
            for line_id, text in patch.changes.items():
                if line_id not in original:
                    raise HTTPException(422, "歌词句不存在")
                if text is not None and (len(text) > 1000 or any(ord(c) < 32 for c in text)):
                    raise HTTPException(422, "每句最多 1000 字，请勿包含换行或控制字符")
                if text is None or text.strip() == original[line_id]:
                    state["changes"].pop(line_id, None)
                else:
                    state["changes"][line_id] = text.strip()
                state.get("reviewed", {}).pop(line_id, None)
            state["revision"] += 1
            write_json(edits_path(folder), state)
            return state

    @app.get("/api/projects/{project_id}/waveforms")
    def envelopes(project_id: str, version: str | None = None):
        result, project = completed(project_id, version)
        path = result / "analysis/ui-waveforms.json"
        hashes = {
            k: sha256(result / project.assets[k]) for k in ("source", "vocals", "instrumental")
        }
        if path.exists():
            cached = read_json(path)
            if cached.get("hashes") == hashes:
                return cached["waveforms"]
        data = {k: waveform(result / project.assets[k]) for k in hashes}
        write_json(path, {"hashes": hashes, "waveforms": data})
        return data

    @app.get("/api/projects/{project_id}/assets/{kind}")
    def asset(project_id: str, kind: str, version: str | None = None):
        result, project = completed(project_id, version)
        if kind in ("project", "lrc", "srt", "midi") and edits_state(result)["changes"]:
            with manager.lock:
                selected = edited_project(result, project)
                folder = result / "user-exports" / fingerprint(selected.lyrics.model_dump())[:16]
                if not (folder / "project.json").exists():
                    export_project(selected, folder)
                    write_json(folder / "project.json", selected.model_dump())
                path = (
                    folder
                    / {
                        "project": "project.json",
                        "lrc": "exports/lyrics.lrc",
                        "srt": "exports/lyrics.srt",
                        "midi": "exports/melody.mid",
                    }[kind]
                )
                return FileResponse(path, filename=path.name)
        if kind == "project":
            path = result / "project.json"
        elif kind in project.assets:
            path = (result / project.assets[kind]).resolve()
        else:
            raise HTTPException(404, "文件不存在")
        if not path.is_relative_to(result.resolve()) or not path.is_file():
            raise HTTPException(404, "文件不存在")
        return FileResponse(
            path,
            filename=path.name,
            content_disposition_type="inline"
            if kind in ("source", "vocals", "instrumental", "pitch")
            else "attachment",
        )

    static = Path(__file__).parent / "static"
    app.mount("/", StaticFiles(directory=static, html=True), name="ui")
    return app


def serve(
    workspace: Path, settings: Settings, port: int, open_browser: bool, interface: str = "create"
):
    from ..desktop import run

    return run(workspace, settings, port, open_browser, interface)
