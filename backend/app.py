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


@app.on_event("shutdown")
def on_shutdown() -> None:
    logger.info("Depo-Pro backend shutting down.")
