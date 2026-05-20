from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection


def create_speaker_correction(
    *,
    session_id: int,
    speaker_segment_id: int,
    original_speaker_label: str,
    corrected_speaker_label: str,
    corrected_role: str | None,
    reviewer: str,
    note: str | None,
    database_path: Path | None = None,
) -> dict[str, object]:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO speaker_corrections (
                session_id,
                speaker_segment_id,
                original_speaker_label,
                corrected_speaker_label,
                corrected_role,
                reviewer,
                note
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                speaker_segment_id,
                original_speaker_label,
                corrected_speaker_label,
                corrected_role,
                reviewer,
                note,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM speaker_corrections WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def get_latest_speaker_corrections(
    session_id: int,
    database_path: Path | None = None,
) -> dict[int, dict[str, object]]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM speaker_corrections
            WHERE session_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (session_id,),
        ).fetchall()
    latest: dict[int, dict[str, object]] = {}
    for row in rows:
        payload = dict(row)
        segment_id = int(payload["speaker_segment_id"])
        latest.setdefault(segment_id, payload)
    return latest
