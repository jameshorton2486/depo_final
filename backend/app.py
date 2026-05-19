"""Depo-Pro FastAPI application.

Phase B.1: backend scaffold + health endpoint + static UI serving.
Phase B.2 will add SQLite session and case CRUD routers.
Phase B.3 will add the transcription router.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from backend import config
from backend.db import migrations as db_migrations
from backend.db import seeds as db_seeds

app = FastAPI(
    title="Depo-Pro Backend",
    version="0.1.0",
    description="Local-first legal deposition workspace backend.",
)

# CORS - PyWebView runs same-origin, but allow localhost variants for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://{config.BACKEND_HOST}:{config.BACKEND_PORT}",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> JSONResponse:
    """Liveness check. Returns 200 with server metadata when the app is ready."""
    return JSONResponse(
        {
            "status": "ok",
            "service": "depo-pro-backend",
            "version": app.version,
            "phase": "B.1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.get("/health/config")
def health_config() -> JSONResponse:
    """Reports which optional services are configured. Does NOT leak secret values."""
    return JSONResponse(
        {
            "deepgram_configured": bool(config.DEEPGRAM_API_KEY),
            "debug": config.DEBUG,
        }
    )


@app.get("/health/db")
def health_db() -> JSONResponse:
    """Reports SQLite database health: file exists, schema version, table count."""
    db_exists = db_migrations.DB_PATH.exists()
    tables: list[str] = []
    schema_version: int = 0
    if db_exists:
        conn = db_migrations._connect()
        try:
            schema_version = db_migrations.current_version(conn)
            tables = db_migrations.list_tables()
        finally:
            conn.close()
    return JSONResponse({
        "db_exists": db_exists,
        "db_path": str(db_migrations.DB_PATH),
        "schema_version": schema_version,
        "table_count": len(tables),
        "tables": tables,
    })


# Static UI mount - must come AFTER all API routes
# Mounting at "/" so existing frontend fetches like screens/stage_1_intake.html keep working
app.mount("/", StaticFiles(directory=str(config.UI_ROOT), html=True), name="ui")


@app.on_event("startup")
def on_startup() -> None:
    logger.info(
        f"Depo-Pro backend starting on http://{config.BACKEND_HOST}:{config.BACKEND_PORT}"
    )
    logger.info(f"UI root: {config.UI_ROOT}")
    if config.DEEPGRAM_API_KEY:
        logger.info("Deepgram API key detected in environment.")
    else:
        logger.info("Deepgram API key not set (expected until Phase B.3).")

    final_version = db_migrations.apply()
    logger.info(f"DB at {db_migrations.DB_PATH} (schema v{final_version})")
    seed_result = db_seeds.seed()
    logger.info(f"Seed result: {seed_result}")


@app.on_event("shutdown")
def on_shutdown() -> None:
    logger.info("Depo-Pro backend shutting down.")
