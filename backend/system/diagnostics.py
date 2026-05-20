from __future__ import annotations

import json
from pathlib import Path

from backend.config import settings
from backend.database.connection import open_connection
from backend.database.init_db import database_status
from backend.system.cleanup_manager import collect_cleanup_targets
from backend.system.deployment_checklist import build_deployment_checklist
from backend.system.logging_config import ensure_log_root
from backend.system.startup_validation import run_startup_validation
from backend.system.transcript_integrity import (
    check_session_integrity,
    scan_transcript_integrity,
)


def get_system_diagnostics(
    session_id: int | None = None,
    database_path: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, object]:
    startup = run_startup_validation(database_path)
    db_state = database_status(database_path)
    integrity = (
        check_session_integrity(session_id, database_path)
        if session_id is not None
        else scan_transcript_integrity(database_path)
    )
    asset_diagnostics = _asset_diagnostics(database_path)
    return {
        "startup": startup,
        "database": db_state,
        "integrity": integrity,
        "assets": asset_diagnostics,
        "cleanup": collect_cleanup_targets(data_root),
        "deployment": build_deployment_checklist(),
        "logs_root": str(ensure_log_root(data_root)),
        "deepgram_configured": bool(settings.deepgram_api_key),
    }


def _asset_diagnostics(database_path: Path | None = None) -> dict[str, object]:
    missing_files: list[dict[str, object]] = []
    corrupted_json: list[dict[str, object]] = []
    with open_connection(database_path) as connection:
        rows = connection.execute("""
            SELECT
                id,
                session_id,
                asset_type,
                file_path,
                deepgram_json_path,
                preprocessing_metadata_path
            FROM transcript_assets
            ORDER BY id ASC
            """).fetchall()
    for row in rows:
        for field_name in ("file_path", "deepgram_json_path", "preprocessing_metadata_path"):
            value = row[field_name]
            if not value:
                continue
            path = Path(str(value))
            if not path.exists():
                missing_files.append(
                    {
                        "asset_id": row["id"],
                        "session_id": row["session_id"],
                        "field": field_name,
                        "path": str(path),
                    }
                )
                continue
            if field_name.endswith("_json_path") or field_name.endswith("_metadata_path"):
                try:
                    if path.suffix == ".jsonl":
                        for line in path.read_text(encoding="utf-8").splitlines():
                            if line.strip():
                                json.loads(line)
                    else:
                        json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    corrupted_json.append(
                        {
                            "asset_id": row["id"],
                            "session_id": row["session_id"],
                            "field": field_name,
                            "path": str(path),
                        }
                    )
    return {
        "asset_count": len(rows),
        "missing_files": missing_files,
        "missing_file_count": len(missing_files),
        "corrupted_json": corrupted_json,
        "corrupted_json_count": len(corrupted_json),
    }
