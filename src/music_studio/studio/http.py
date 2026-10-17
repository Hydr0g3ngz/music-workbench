"""Thin HTTP adapter; all editing state belongs to StudioService."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from .models import (
    AdoptRequest,
    CompareRequest,
    ExportRequest,
    LocalTaskRequest,
    PreviewRequest,
    RevisionRequest,
    SelectionRequest,
    TranscriptPatch,
)
from .service import StudioError, StudioService


def router(service: StudioService) -> APIRouter:
    api = APIRouter(prefix="/api/projects/{project}/studio")

    def call(function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except StudioError as error:
            raise HTTPException(error.status, str(error)) from error
        except (ValueError, OSError) as error:
            raise HTTPException(422, str(error)) from error

    @api.get("")
    def session(project: str):
        return call(service.session, project)

    @api.post("/preview", status_code=201)
    def preview(project: str, request: PreviewRequest):
        return call(service.preview, project, request)

    @api.post("/selection")
    def selection(project: str, request: SelectionRequest):
        return call(service.selection, project, request)

    @api.post("/compare")
    def compare(project: str, request: CompareRequest):
        return call(service.comparison, project, request.reference, request.processed)

    @api.post("/adopt")
    def adopt(project: str, request: AdoptRequest):
        return call(service.adopt, project, request.candidate, request.revision)

    @api.post("/history/{direction}")
    def history(project: str, direction: str, request: RevisionRequest):
        return call(service.history, project, request.revision, direction)

    @api.get("/events")
    def events(project: str, after: Annotated[int, Query(ge=0)] = 0):
        return call(service.events, project, after)

    @api.get("/models")
    def models(project: str):
        call(service.project_dir, project)
        return call(service.tasks.registry.list)

    @api.post("/models/{model}/check")
    def check_model(project: str, model: str):
        call(service.project_dir, project)
        return call(service.tasks.registry.check, model)

    @api.get("/tasks")
    def tasks(project: str):
        return call(service.tasks.list, project)

    @api.post("/tasks", status_code=202)
    def submit_task(project: str, request: LocalTaskRequest):
        return call(service.tasks.submit, project, request)

    @api.post("/tasks/{task}/cancel")
    def cancel_task(project: str, task: str):
        return call(service.tasks.cancel, project, task)

    @api.get("/tasks/{task}/input")
    def task_input(project: str, task: str):
        return FileResponse(call(service.tasks.input_path, project, task), media_type="audio/wav")

    @api.get("/artifacts/{asset}")
    def artifact(project: str, asset: str, download: bool = False):
        path, record = call(service.tasks.artifact_path, project, asset)
        return FileResponse(
            path,
            media_type=record["mime"],
            filename=path.name if download else None,
            content_disposition_type="attachment" if download else "inline",
        )

    @api.post("/transcripts/{asset}", status_code=201)
    def correct_transcript(project: str, asset: str, request: TranscriptPatch):
        from .transcripts import correct

        return call(correct, service, project, asset, request)

    @api.get("/assets/{asset}")
    def audio(project: str, asset: str):
        path = call(service.asset_path, project, asset)
        return FileResponse(path, media_type="audio/ogg" if path.suffix == ".ogg" else "audio/wav")

    @api.get("/assets/{asset}/info")
    def audio_info(project: str, asset: str):
        from . import dsp

        path = call(service.asset_path, project, asset)
        return {"audio": call(dsp.inspect_audio, path), "waveform": call(dsp.peaks, path)}

    @api.post("/export", status_code=201)
    def export(project: str, request: ExportRequest):
        result = call(service.export, project, request.revision, request.asset, request.subtype)
        result["url"] = f"/api/projects/{project}/studio/exports/{result['id']}"
        return result

    @api.get("/exports/{export_id}")
    def download(project: str, export_id: str):
        import re

        if not re.fullmatch(r"[a-f0-9]{16}", export_id):
            raise HTTPException(404, "Export does not exist")
        path = call(
            service.safe_file, service.project_dir(project), f".studio/exports/{export_id}.wav"
        )
        return FileResponse(path, media_type="audio/wav", filename=f"music-studio-{export_id}.wav")

    @api.get("/recipe/{candidate}")
    def recipe(project: str, candidate: str):
        # Export only the reusable operations; project files and paths are excluded.
        session = call(service.session, project)
        match = next((c for c in session["candidates"] if c["id"] == candidate), None)
        if match is None:
            raise HTTPException(404, "Preview does not exist")
        return {"format": "music-studio-recipe", "version": 1, "operations": match["operations"]}

    return api
