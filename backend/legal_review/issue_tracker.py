from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection
from backend.legal_review.legal_navigation import insert_navigation_entry


def create_review_issue(
    *,
    session_id: int,
    review_category: str,
    transcript_block_id: int | None = None,
    word_object_id: int | None = None,
    reviewer: str | None = None,
    note: str | None = None,
    issue_status: str = "open",
    priority: str = "normal",
    database_path: Path | None = None,
) -> dict[str, object]:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO review_issues (
                session_id,
                transcript_block_id,
                word_object_id,
                review_category,
                issue_status,
                priority,
                reviewer,
                note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                transcript_block_id,
                word_object_id,
                review_category,
                issue_status,
                priority,
                reviewer,
                note,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM review_issues WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    issue = dict(row)
    insert_navigation_entry(
        session_id=session_id,
        nav_type="ISSUE",
        nav_label=review_category,
        transcript_block_id=transcript_block_id,
        word_object_id=word_object_id,
        reference_id=int(issue["id"]),
        event_time=_resolve_event_time(session_id, transcript_block_id, database_path),
        database_path=database_path,
    )
    return issue


def list_review_issues(
    session_id: int,
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM review_issues
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
