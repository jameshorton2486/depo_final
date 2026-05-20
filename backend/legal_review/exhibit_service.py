from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from backend.database.connection import open_connection
from backend.legal_review.legal_navigation import insert_navigation_entry


class ExhibitLinkCreate(BaseModel):
    session_id: int
    transcript_block_id: int
    exhibit_label: str
    exhibit_description: str | None = None
    exhibit_path: str | None = None
    created_by: str


def create_exhibit_link(
    payload: ExhibitLinkCreate,
    database_path: Path | None = None,
) -> dict[str, object]:
    event_time = _block_start_time(payload.session_id, payload.transcript_block_id, database_path)
    with open_connection(database_path) as connection:
        exhibit_row = connection.execute(
            """
            SELECT *
            FROM exhibits
            WHERE session_id = ? AND exhibit_label = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (payload.session_id, payload.exhibit_label),
        ).fetchone()
        if exhibit_row is None:
            exhibit_cursor = connection.execute(
                """
                INSERT INTO exhibits (session_id, exhibit_label, exhibit_path, description)
                VALUES (?, ?, ?, ?)
                """,
                (
                    payload.session_id,
                    payload.exhibit_label,
                    payload.exhibit_path,
                    payload.exhibit_description,
                ),
            )
            exhibit_row = connection.execute(
                "SELECT * FROM exhibits WHERE id = ?",
                (exhibit_cursor.lastrowid,),
            ).fetchone()
        cursor = connection.execute(
            """
            INSERT INTO linked_exhibits (
                session_id,
                transcript_block_id,
                exhibit_id,
                exhibit_label,
                exhibit_description,
                event_time,
                created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.session_id,
                payload.transcript_block_id,
                exhibit_row["id"],
                payload.exhibit_label,
                payload.exhibit_description,
                event_time,
                payload.created_by,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM linked_exhibits WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    linked = dict(row)
    insert_navigation_entry(
        session_id=payload.session_id,
        nav_type="EXHIBIT",
        nav_label=payload.exhibit_label,
        transcript_block_id=payload.transcript_block_id,
        reference_id=int(linked["id"]),
        event_time=event_time,
        database_path=database_path,
    )
    return {"linked_exhibit": linked, "exhibit": dict(exhibit_row)}


def list_linked_exhibits(
    session_id: int,
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM linked_exhibits
            WHERE session_id = ?
            ORDER BY COALESCE(event_time, 0.0) ASC, id ASC
            """,
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _block_start_time(
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
    if row is None:
        raise LookupError(f"Transcript block {transcript_block_id} was not found.")
    return float(row["start_time"])
