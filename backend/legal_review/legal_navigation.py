from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection


def insert_navigation_entry(
    *,
    session_id: int,
    nav_type: str,
    nav_label: str,
    transcript_block_id: int | None = None,
    word_object_id: int | None = None,
    reference_id: int | None = None,
    event_time: float | None = None,
    database_path: Path | None = None,
) -> dict[str, object]:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO legal_navigation_index (
                session_id,
                nav_type,
                nav_label,
                transcript_block_id,
                word_object_id,
                reference_id,
                event_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                nav_type,
                nav_label,
                transcript_block_id,
                word_object_id,
                reference_id,
                event_time,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM legal_navigation_index WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def get_navigation_index(
    session_id: int,
    database_path: Path | None = None,
) -> dict[str, object]:
    persisted = _get_persisted_navigation(session_id, database_path)
    speakers = _get_speaker_navigation(session_id, database_path)
    items = sorted(
        [*persisted, *speakers],
        key=lambda item: (
            float(item.get("event_time") or 0.0),
            str(item.get("nav_type") or ""),
            int(item.get("id") or 0),
        ),
    )
    return {
        "session_id": session_id,
        "items": items,
        "by_type": _group_by_type(items),
    }


def _get_persisted_navigation(
    session_id: int,
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM legal_navigation_index
            WHERE session_id = ?
            ORDER BY COALESCE(event_time, 0.0) ASC, id ASC
            """,
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _get_speaker_navigation(
    session_id: int,
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                MIN(transcript_blocks.id) AS transcript_block_id,
                MIN(transcript_blocks.start_time) AS event_time,
                COALESCE(speaker_segments.speaker_label, 'Speaker') AS nav_label
            FROM transcript_blocks
            LEFT JOIN speaker_segments
                ON speaker_segments.id = transcript_blocks.speaker_segment_id
            WHERE transcript_blocks.session_id = ?
            GROUP BY COALESCE(speaker_segments.speaker_label, 'Speaker')
            ORDER BY MIN(transcript_blocks.start_time) ASC
            """,
            (session_id,),
        ).fetchall()
    return [
        {
            "id": None,
            "session_id": session_id,
            "nav_type": "SPEAKER",
            "nav_label": row["nav_label"],
            "transcript_block_id": row["transcript_block_id"],
            "word_object_id": None,
            "reference_id": None,
            "event_time": row["event_time"],
        }
        for row in rows
    ]


def _group_by_type(items: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    groups: dict[str, list[dict[str, object]]] = {}
    for item in items:
        groups.setdefault(str(item.get("nav_type") or "UNKNOWN"), []).append(item)
    return groups
