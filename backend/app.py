from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database.init_db import database_status, initialize_database
from backend.review.audit_logger import list_audit_events
from backend.review.confidence_queue import ensure_review_queue
from backend.review.correction_engine import resolve_review_action
from backend.review.review_state import ReviewResolveRequest
from backend.review.transcript_query_service import (
    get_review_media_path,
    get_review_timeline,
    get_review_word,
)
from backend.services.intake_service import IntakeParseRequest, get_intake, parse_and_persist
from backend.transcript.transcript_service import (
    TranscriptionRequest,
    get_transcript,
    transcribe_and_persist,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/api/db/status")
async def db_status() -> dict[str, bool | str]:
    return database_status()


@app.post("/api/intake/parse")
async def parse_intake(request: IntakeParseRequest) -> dict[str, object]:
    try:
        return parse_and_persist(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/intake/{case_id}")
async def intake_details(case_id: int) -> dict[str, object]:
    try:
        return get_intake(case_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/transcribe/prerecorded")
async def transcribe_prerecorded(request: TranscriptionRequest) -> dict[str, object]:
    try:
        return transcribe_and_persist(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/transcript/{session_id}")
async def transcript_details(session_id: int) -> dict[str, object]:
    try:
        return get_transcript(session_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/transcript/{session_id}/timeline")
async def transcript_timeline(session_id: int) -> dict[str, object]:
    try:
        return get_review_timeline(session_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/transcript/{session_id}/word/{word_id}")
async def transcript_word(session_id: int, word_id: int) -> dict[str, object]:
    try:
        return get_review_word(session_id, word_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/transcript/{session_id}/media")
async def transcript_media(session_id: int) -> FileResponse:
    try:
        media_path = get_review_media_path(session_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path=media_path)


@app.get("/api/review/{session_id}/queue")
async def review_queue(session_id: int) -> dict[str, object]:
    try:
        queue = ensure_review_queue(session_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"session_id": session_id, "items": queue}


@app.post("/api/review/resolve")
async def review_resolve(request: ReviewResolveRequest) -> dict[str, object]:
    try:
        return resolve_review_action(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/review/{session_id}/audit")
async def review_audit(session_id: int) -> dict[str, object]:
    return {"session_id": session_id, "items": list_audit_events(session_id)}


app.mount(
    "/",
    StaticFiles(directory=str(settings.frontend_root), html=True),
    name="frontend",
)
