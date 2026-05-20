from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from backend.config import settings
from backend.database.connection import open_connection
from backend.database.repositories.sessions_repo import get_session
from backend.export.export_service import get_export_history
from backend.system.cleanup_manager import collect_cleanup_targets
from backend.system.logging_config import write_log_event
from backend.system.transcript_integrity import check_session_integrity
from backend.transcript.transcript_service import get_transcript


class RecoveryRequest(BaseModel):
    action: str = "scan"
    session_id: int | None = None


def run_recovery(
    request: RecoveryRequest,
    database_path: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, object]:
    if request.action == "scan":
        payload = _scan_recovery_state(database_path, data_root)
    elif request.action == "checkpoint":
        if request.session_id is None:
            raise ValueError("session_id is required for checkpoint recovery.")
        payload = create_recovery_checkpoint(request.session_id, database_path, data_root)
    elif request.action == "cleanup":
        payload = collect_cleanup_targets(data_root)
    else:
        raise ValueError(f"Unsupported recovery action: {request.action}")

    write_log_event(
        "system_recovery",
        f"recovery_action:{request.action}",
        payload={
            "session_id": request.session_id or 0,
            "result_keys": ",".join(sorted(payload.keys())),
        },
        data_root=data_root,
    )
    return {"action": request.action, "result": payload}


def create_recovery_checkpoint(
    session_id: int,
    database_path: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, object]:
    resolved_root = data_root if data_root is not None else settings.data_root
    session_record = get_session(session_id, database_path)
    transcript_bundle = get_transcript(session_id, database_path)
    integrity = check_session_integrity(session_id, database_path)
    history = get_export_history(session_id, database_path, resolved_root)
    checkpoint_root = (
        resolved_root / "cases" / str(session_record.case_id) / "recovery" / f"session_{session_id}"
    )
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    checkpoint_path = checkpoint_root / f"checkpoint_{timestamp}.json"
    payload = {
        "session_id": session_id,
        "case_id": session_record.case_id,
        "created_at": timestamp,
        "integrity": integrity,
        "transcript_summary": {
            "asset_count": len(transcript_bundle["assets"]),
            "block_count": len(transcript_bundle["transcript_blocks"]),
            "word_count": len(transcript_bundle["word_objects"]),
            "speaker_segment_count": len(transcript_bundle["speaker_segments"]),
        },
        "export_history_count": len(history["items"]),
    }
    checkpoint_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "checkpoint_path": str(checkpoint_path),
        "summary": payload,
    }


def _scan_recovery_state(
    database_path: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, object]:
    resolved_root = data_root if data_root is not None else settings.data_root
    interrupted_transcriptions: list[dict[str, object]] = []
    failed_uploads: list[dict[str, object]] = []
    partial_exports: list[dict[str, object]] = []
    reconnect_candidates: list[dict[str, object]] = []
    with open_connection(database_path) as connection:
        asset_rows = connection.execute("""
            SELECT
                transcript_assets.id,
                transcript_assets.session_id,
                transcript_assets.file_path,
                transcript_assets.deepgram_json_path,
                transcript_assets.preprocessing_metadata_path,
                COUNT(transcript_blocks.id) AS block_count
            FROM transcript_assets
            LEFT JOIN transcript_blocks
                ON transcript_blocks.session_id = transcript_assets.session_id
            GROUP BY transcript_assets.id
            ORDER BY transcript_assets.id ASC
            """).fetchall()
        event_rows = connection.execute("""
            SELECT session_id, event_type, created_at
            FROM session_events
            WHERE event_type IN ('realtime_started', 'realtime_stopped')
            ORDER BY session_id ASC, id ASC
            """).fetchall()

    for row in asset_rows:
        if int(row["block_count"] or 0) == 0:
            interrupted_transcriptions.append(
                {"asset_id": row["id"], "session_id": row["session_id"]}
            )
        file_path = Path(str(row["file_path"]))
        if not file_path.exists():
            failed_uploads.append(
                {
                    "asset_id": row["id"],
                    "session_id": row["session_id"],
                    "missing_path": str(file_path),
                }
            )

    events_by_session: dict[int, list[str]] = {}
    for row in event_rows:
        events_by_session.setdefault(int(row["session_id"]), []).append(str(row["event_type"]))
    for session_id, events in events_by_session.items():
        if "realtime_started" in events and "realtime_stopped" not in events:
            reconnect_candidates.append({"session_id": session_id, "events": events})

    for manifest_parent in resolved_root.glob("cases/*/exports/session_*/*"):
        if not manifest_parent.is_dir():
            continue
        manifest_path = manifest_parent / "export_manifest.json"
        if not manifest_path.exists():
            partial_exports.append({"path": str(manifest_parent)})

    return {
        "interrupted_transcriptions": interrupted_transcriptions,
        "failed_uploads": failed_uploads,
        "partial_exports": partial_exports,
        "reconnect_candidates": reconnect_candidates,
    }
