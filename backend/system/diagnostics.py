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
    review_diagnostics = _review_diagnostics(database_path)
    export_diagnostics = _export_diagnostics(data_root)
    realtime_diagnostics = _realtime_diagnostics(database_path)
    summary = {
        "sessions_scanned": integrity.get("session_count", 0),
        "integrity_issue_count": integrity.get("issue_count", 0),
        "orphan_transcript_count": _integrity_issue_count(integrity, "ORPHANED_TRANSCRIPT_BLOCK"),
        "overlap_issue_count": _integrity_issue_count(integrity, "OVERLAPPING_BLOCKS"),
        "missing_asset_count": asset_diagnostics["missing_file_count"],
        "corrupted_json_count": asset_diagnostics["corrupted_json_count"],
        "export_failure_count": export_diagnostics["partial_export_count"],
        "realtime_reconnect_count": realtime_diagnostics["reconnect_candidate_count"],
        "database_health": db_state["database"],
        "tables_initialized": db_state["tables_initialized"],
        "review_queue_count": review_diagnostics["open_review_flag_count"],
    }
    return {
        "summary": summary,
        "startup": startup,
        "database": db_state,
        "integrity": integrity,
        "assets": asset_diagnostics,
        "review": review_diagnostics,
        "exports": export_diagnostics,
        "realtime": realtime_diagnostics,
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


def _review_diagnostics(database_path: Path | None = None) -> dict[str, object]:
    with open_connection(database_path) as connection:
        review_flag_count = connection.execute(
            "SELECT COUNT(*) AS count FROM review_flags WHERE status = 'open'"
        ).fetchone()["count"]
        session_count = connection.execute("SELECT COUNT(*) AS count FROM sessions").fetchone()[
            "count"
        ]
    return {
        "open_review_flag_count": int(review_flag_count or 0),
        "session_count": int(session_count or 0),
    }


def _export_diagnostics(data_root: Path | None = None) -> dict[str, object]:
    resolved_root = data_root if data_root is not None else settings.data_root
    partial_exports: list[str] = []
    export_manifest_count = 0
    for _manifest_path in resolved_root.glob("cases/*/exports/session_*/*/export_manifest.json"):
        export_manifest_count += 1
    for export_dir in resolved_root.glob("cases/*/exports/session_*/*"):
        if export_dir.is_dir() and not (export_dir / "export_manifest.json").exists():
            partial_exports.append(str(export_dir))
    return {
        "manifest_count": export_manifest_count,
        "partial_exports": partial_exports,
        "partial_export_count": len(partial_exports),
    }


def _realtime_diagnostics(database_path: Path | None = None) -> dict[str, object]:
    reconnect_candidates: list[int] = []
    with open_connection(database_path) as connection:
        rows = connection.execute("""
            SELECT session_id, event_type
            FROM session_events
            WHERE event_type IN ('realtime_started', 'realtime_stopped')
            ORDER BY session_id ASC, id ASC
            """).fetchall()
    events_by_session: dict[int, list[str]] = {}
    for row in rows:
        events_by_session.setdefault(int(row["session_id"]), []).append(str(row["event_type"]))
    for session_id, events in events_by_session.items():
        if "realtime_started" in events and "realtime_stopped" not in events:
            reconnect_candidates.append(session_id)
    return {
        "reconnect_candidates": reconnect_candidates,
        "reconnect_candidate_count": len(reconnect_candidates),
        "healthy": len(reconnect_candidates) == 0,
    }


def _integrity_issue_count(integrity: dict[str, object], code: str) -> int:
    reports = integrity.get("reports", [])
    count = 0
    for report in reports:
        for issue in report.get("issues", []):
            if issue.get("code") == code:
                count += 1
    return count
