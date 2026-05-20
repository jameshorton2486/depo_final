from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from backend.database.connection import open_connection
from backend.legal_review.issue_tracker import create_review_issue
from backend.legal_review.legal_navigation import insert_navigation_entry


class ObjectionCreate(BaseModel):
    session_id: int
    transcript_block_id: int
    category: str
    objection_text: str
    reviewer: str
    colloquy_group: str | None = None


def create_objection(
    payload: ObjectionCreate,
    database_path: Path | None = None,
) -> dict[str, object]:
    block_meta = _block_meta(payload.session_id, payload.transcript_block_id, database_path)
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO objections (
                session_id,
                transcript_block_id,
                speaker_segment_id,
                category,
                objection_text,
                colloquy_group,
                reviewer,
                event_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.session_id,
                payload.transcript_block_id,
                block_meta["speaker_segment_id"],
                payload.category,
                payload.objection_text,
                payload.colloquy_group,
                payload.reviewer,
                block_meta["start_time"],
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM objections WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    objection = dict(row)
    issue = create_review_issue(
        session_id=payload.session_id,
        transcript_block_id=payload.transcript_block_id,
        review_category=f"OBJECTION_{payload.category}",
        reviewer=payload.reviewer,
        note=payload.objection_text,
        database_path=database_path,
    )
    insert_navigation_entry(
        session_id=payload.session_id,
        nav_type="OBJECTION",
        nav_label=payload.category,
        transcript_block_id=payload.transcript_block_id,
        reference_id=int(objection["id"]),
        event_time=float(block_meta["start_time"]),
        database_path=database_path,
    )
    return {"objection": objection, "issue": issue}


def list_objections(
    session_id: int,
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM objections
            WHERE session_id = ?
            ORDER BY COALESCE(event_time, 0.0) ASC, id ASC
            """,
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _block_meta(
    session_id: int,
    transcript_block_id: int,
    database_path: Path | None = None,
) -> dict[str, object]:
    with open_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT speaker_segment_id, start_time
            FROM transcript_blocks
            WHERE session_id = ? AND id = ?
            """,
            (session_id, transcript_block_id),
        ).fetchone()
    if row is None:
        raise LookupError(f"Transcript block {transcript_block_id} was not found.")
    return dict(row)
