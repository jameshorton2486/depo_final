from __future__ import annotations

from pathlib import Path

from backend.config import settings
from backend.system.startup_validation import run_startup_validation
from backend.system.transcript_integrity import scan_transcript_integrity


def get_system_health(database_path: Path | None = None) -> dict[str, object]:
    startup = run_startup_validation(database_path)
    integrity = scan_transcript_integrity(database_path)
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "database": "connected" if startup["checks"]["database_initialized"] else "error",
        "startup_valid": startup["ok"],
        "transcript_integrity_ok": integrity["ok"],
        "session_count": integrity["session_count"],
        "integrity_issue_count": integrity["issue_count"],
        "deepgram_configured": bool(settings.deepgram_api_key),
        "mode": "mock" if settings.transcribe_mock else "standard",
        "status": "ok" if startup["ok"] and integrity["ok"] else "warning",
    }
