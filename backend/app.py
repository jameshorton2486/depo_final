from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database.init_db import database_status, initialize_database
from backend.export.export_service import (
    ExportRequest,
    export_docx_bundle,
    export_package_bundle,
    export_txt_bundle,
    get_export_history,
)
from backend.legal_review import (
    AnnotationCreate,
    ExhibitLinkCreate,
    ObjectionCreate,
    create_annotation,
    create_exhibit_link,
    create_objection,
    get_navigation_index,
    get_review_dashboard,
)
from backend.realtime.realtime_service import (
    RealtimeStartRequest,
    RealtimeStopRequest,
    get_realtime_status,
    realtime_manager,
    start_realtime_session,
    stop_realtime_session,
)
from backend.review.audit_logger import list_audit_events
from backend.review.confidence_queue import ensure_review_queue
from backend.review.correction_engine import resolve_review_action
from backend.review.review_state import ReviewResolveRequest
from backend.review.transcript_query_service import (
    get_review_media_path,
    get_review_timeline,
    get_review_word,
)
from backend.services.intake_service import (
    IntakeParseRequest,
    get_intake,
    list_intake_cases,
    parse_and_persist,
    update_case_stage,
)
from backend.system.diagnostics import get_system_diagnostics
from backend.system.health_monitor import get_system_health
from backend.system.performance_metrics import get_performance_metrics
from backend.system.recovery_manager import RecoveryRequest, run_recovery
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


@app.get("/api/system/health")
async def system_health() -> dict[str, object]:
    return get_system_health()


@app.get("/api/system/diagnostics")
async def system_diagnostics(session_id: int | None = None) -> dict[str, object]:
    return get_system_diagnostics(session_id=session_id)


@app.get("/api/system/performance")
async def system_performance(session_id: int | None = None) -> dict[str, object]:
    return get_performance_metrics(session_id=session_id)


@app.post("/api/system/recovery")
async def system_recovery(request: RecoveryRequest) -> dict[str, object]:
    try:
        return run_recovery(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/db/status")
async def db_status() -> dict[str, bool | str]:
    return database_status()


@app.post("/api/intake/parse")
async def parse_intake(request: IntakeParseRequest) -> dict[str, object]:
    try:
        return parse_and_persist(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/intake/cases")
async def intake_cases() -> dict[str, object]:
    return list_intake_cases()


@app.get("/api/intake/{case_id}")
async def intake_details(case_id: int) -> dict[str, object]:
    try:
        return get_intake(case_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/intake/{case_id}/stage")
async def intake_stage(case_id: int, payload: dict[str, int]) -> dict[str, object]:
    try:
        return update_case_stage(case_id, int(payload.get("stage_id", 1)))
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


@app.post("/api/review/annotation")
async def review_annotation(request: AnnotationCreate) -> dict[str, object]:
    try:
        return create_annotation(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/review/objection")
async def review_objection(request: ObjectionCreate) -> dict[str, object]:
    try:
        return create_objection(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/review/exhibit-link")
async def review_exhibit_link(request: ExhibitLinkCreate) -> dict[str, object]:
    try:
        return create_exhibit_link(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/review/{session_id}/dashboard")
async def review_dashboard(session_id: int) -> dict[str, object]:
    return get_review_dashboard(session_id)


@app.get("/api/review/{session_id}/navigation")
async def review_navigation(session_id: int) -> dict[str, object]:
    return get_navigation_index(session_id)


@app.post("/api/export/docx")
async def export_docx(request: ExportRequest) -> dict[str, object]:
    try:
        return export_docx_bundle(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/export/txt")
async def export_txt(request: ExportRequest) -> dict[str, object]:
    try:
        return export_txt_bundle(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/export/package")
async def export_package(request: ExportRequest) -> dict[str, object]:
    try:
        return export_package_bundle(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/export/{session_id}/history")
async def export_history(session_id: int) -> dict[str, object]:
    try:
        return get_export_history(session_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/realtime/start")
async def realtime_start(request: RealtimeStartRequest) -> dict[str, object]:
    try:
        return await start_realtime_session(request)
    except (LookupError, ValueError) as exc:
        status_code = 404 if isinstance(exc, LookupError) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@app.post("/api/realtime/stop")
async def realtime_stop(request: RealtimeStopRequest) -> dict[str, object]:
    try:
        return await stop_realtime_session(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/realtime/status/{session_id}")
async def realtime_status(session_id: int) -> dict[str, object]:
    try:
        return get_realtime_status(session_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.websocket("/ws/transcript/{session_id}")
async def transcript_websocket(websocket: WebSocket, session_id: int) -> None:
    await realtime_manager.websocket_session(websocket, session_id)


app.mount(
    "/",
    StaticFiles(directory=str(settings.frontend_root), html=True),
    name="frontend",
)
