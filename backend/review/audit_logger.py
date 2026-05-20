from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection


def log_audit_event(
    *,
    session_id: int,
    entity_type: str,
    entity_id: int,
    action_type: str,
    issue_category: str | None,
    original_value: str | None,
    modified_value: str | None,
    reviewer: str,
    correction_source: str,
    database_path: Path | None = None,
) -> dict[str, object]:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO transcript_audit_log (
                session_id,
                entity_type,
                entity_id,
                action_type,
                issue_category,
                original_value,
                modified_value,
                reviewer,
                correction_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                entity_type,
                entity_id,
                action_type,
                issue_category,
                original_value,
                modified_value,
                reviewer,
                correction_source,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM transcript_audit_log WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def list_audit_events(
    session_id: int, database_path: Path | None = None
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM transcript_audit_log
            WHERE session_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]
