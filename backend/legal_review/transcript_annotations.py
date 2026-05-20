from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from backend.database.connection import open_connection
from backend.legal_review.issue_tracker import create_review_issue
from backend.legal_review.legal_navigation import insert_navigation_entry


class AnnotationCreate(BaseModel):
    session_id: int
    transcript_block_id: int | None = None
    word_object_id: int | None = None
    annotation_type: str = "NOTE"
    annotation_text: str
    bookmark_label: str | None = None
    issue_category: str | None = None
    status: str = "open"
    author: str


def create_annotation(
    payload: AnnotationCreate,
    database_path: Path | None = None,
) -> dict[str, object]:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO transcript_annotations (
                session_id,
                transcript_block_id,
                word_object_id,
                annotation_type,
                annotation_text,
                bookmark_label,
                issue_category,
                status,
                author
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.session_id,
                payload.transcript_block_id,
                payload.word_object_id,
                payload.annotation_type,
                payload.annotation_text,
                payload.bookmark_label,
                payload.issue_category,
                payload.status,
                payload.author,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM transcript_annotations WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    annotation = dict(row)
    if payload.annotation_type.upper() == "BOOKMARK" or payload.bookmark_label:
        insert_navigation_entry(
            session_id=payload.session_id,
            nav_type="BOOKMARK",
            nav_label=payload.bookmark_label or payload.annotation_text,
            transcript_block_id=payload.transcript_block_id,
            word_object_id=payload.word_object_id,
            reference_id=int(annotation["id"]),
            event_time=_resolve_event_time(
                payload.session_id, payload.transcript_block_id, database_path
            ),
            database_path=database_path,
        )
    if payload.issue_category:
        create_review_issue(
            session_id=payload.session_id,
            transcript_block_id=payload.transcript_block_id,
            word_object_id=payload.word_object_id,
            review_category=payload.issue_category,
            reviewer=payload.author,
            note=payload.annotation_text,
            database_path=database_path,
        )
    return annotation


def list_annotations(
    session_id: int,
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM transcript_annotations
            WHERE session_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _resolve_event_time(
    session_id: int,
    transcript_block_id: int | None,
    database_path: Path | None = None,
) -> float | None:
    if transcript_block_id is None:
        return None
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
