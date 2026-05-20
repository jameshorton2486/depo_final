from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database.init_db import database_status, initialize_database
from backend.services.intake_service import IntakeParseRequest, get_intake, parse_and_persist


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


app.mount(
    "/",
    StaticFiles(directory=str(settings.frontend_root), html=True),
    name="frontend",
)
