from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database.init_db import database_status, initialize_database


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


app.mount(
    "/",
    StaticFiles(directory=str(settings.frontend_root), html=True),
    name="frontend",
)
