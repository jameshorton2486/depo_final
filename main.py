"""Depo-Pro desktop launcher (Phase B.1).

Starts the FastAPI backend on a background thread, then opens PyWebView
pointing at the FastAPI server URL. The backend serves both the API
(routes under /health, future /cases, /sessions, etc.) and the static UI
files via FastAPI's StaticFiles mount.

The stdlib http.server from Phase A.1 is no longer used.
"""
from __future__ import annotations

import threading
import time

import uvicorn
import webview
from loguru import logger

from backend import config
from backend.app import app as fastapi_app

WINDOW_TITLE = "Depo-Pro"
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1000
MIN_WIDTH = 1280
MIN_HEIGHT = 800


def run_backend() -> None:
    """Run the FastAPI server. Called on a background daemon thread."""
    uvicorn.run(
        fastapi_app,
        host=config.BACKEND_HOST,
        port=config.BACKEND_PORT,
        log_level="info" if config.DEBUG else "warning",
        access_log=config.DEBUG,
    )


def main() -> None:
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()

    time.sleep(0.6)

    backend_url = f"http://{config.BACKEND_HOST}:{config.BACKEND_PORT}/index.html"
    logger.info(f"Opening PyWebView at {backend_url}")

    webview.create_window(
        title=WINDOW_TITLE,
        url=backend_url,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
    )
    webview.start(debug=config.DEBUG)


if __name__ == "__main__":
    main()
