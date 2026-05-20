from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection
from backend.legal_review.legal_navigation import insert_navigation_entry


def ensure_interpreted_segments(
    session_id: int,
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        existing_block_ids = {
            row["transcript_block_id"]
            for row in connection.execute(
                """
                SELECT transcript_block_id
                FROM interpreted_segments
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchall()
        }
        rows = connection.execute(
            """
            SELECT
                transcript_blocks.id AS transcript_block_id,
                transcript_blocks.raw_text,
                transcript_blocks.start_time,
                transcript_blocks.speaker_segment_id,
                speaker_segments.speaker_label
            FROM transcript_blocks
            LEFT JOIN speaker_segments
                ON speaker_segments.id = transcript_blocks.speaker_segment_id
            WHERE transcript_blocks.session_id = ?
              AND (
                transcript_blocks.block_type = 'INTERPRETER_STATEMENT'
                OR UPPER(COALESCE(speaker_segments.speaker_label, '')) LIKE 'THE INTERPRETER%'
              )
            ORDER BY transcript_blocks.block_index ASC
            """,
            (session_id,),
        ).fetchall()
        created: list[dict[str, object]] = []
        for row in rows:
            if row["transcript_block_id"] in existing_block_ids:
                continue
            cursor = connection.execute(
                """
                INSERT INTO interpreted_segments (
                    session_id,
                    transcript_block_id,
                    speaker_segment_id,
                    interpreter_label,
                    source_language,
                    target_language,
                    interpreted_text,
                    created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    row["transcript_block_id"],
                    row["speaker_segment_id"],
                    row["speaker_label"] or "THE INTERPRETER",
                    "Unknown",
                    "English",
                    row["raw_text"],
                    "system",
                ),
            )
            created_row = connection.execute(
                "SELECT * FROM interpreted_segments WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
            created.append(dict(created_row))
        connection.commit()

    for item in created:
        insert_navigation_entry(
            session_id=session_id,
            nav_type="INTERPRETED",
            nav_label=item["interpreter_label"] or "THE INTERPRETER",
            transcript_block_id=int(item["transcript_block_id"]),
            reference_id=int(item["id"]),
            event_time=_event_time_for_block(
                session_id, int(item["transcript_block_id"]), database_path
            ),
            database_path=database_path,
        )
    return list_interpreted_segments(session_id, database_path)


def list_interpreted_segments(
    session_id: int,
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM interpreted_segments
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _event_time_for_block(
    session_id: int,
    transcript_block_id: int,
    database_path: Path | None = None,
) -> float | None:
    with open_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT start_time
            FROM transcript_blocks
            WHERE session_id = ? AND id = ?
            """,
            (session_id, transcript_block_id),
        ).fetchone()
    return float(row["start_time"]) if row else None
