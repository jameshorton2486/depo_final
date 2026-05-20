from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from backend.database.connection import open_connection
from backend.database.models.transcript_models import ReviewIssueCategory


class ReviewResolveRequest(BaseModel):
    session_id: int
    review_flag_id: int
    action: str
    reviewer: str
    note: str | None = None
    issue_category: ReviewIssueCategory | None = None
    corrected_speaker_label: str | None = None
    corrected_role: str | None = None
    apply_deterministic_rules: bool = False
    reviewer_metadata: dict[str, object] = Field(default_factory=dict)


def ensure_review_session(
    session_id: int,
    reviewer: str,
    database_path: Path | None = None,
) -> dict[str, object]:
    with open_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM review_sessions
            WHERE session_id = ? AND reviewer = ? AND status = 'in_progress'
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id, reviewer),
        ).fetchone()
        if row is None:
            cursor = connection.execute(
                """
                INSERT INTO review_sessions (session_id, reviewer, reviewer_notes)
                VALUES (?, ?, ?)
                """,
                (session_id, reviewer, None),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM review_sessions WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
    return dict(row)


def get_review_flag(review_flag_id: int, database_path: Path | None = None) -> dict[str, object]:
    with open_connection(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM review_flags WHERE id = ?",
            (review_flag_id,),
        ).fetchone()
    if row is None:
        raise LookupError(f"Review flag {review_flag_id} was not found.")
    return dict(row)


def update_review_flag(
    review_flag_id: int,
    *,
    status: str,
    note: str | None,
    current_value: str | None,
    reviewer: str,
    database_path: Path | None = None,
) -> dict[str, object]:
    with open_connection(database_path) as connection:
        connection.execute(
            """
            UPDATE review_flags
            SET status = ?,
                note = ?,
                current_value = ?,
                reviewer = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, note, current_value, reviewer, review_flag_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM review_flags WHERE id = ?",
            (review_flag_id,),
        ).fetchone()
    if row is None:
        raise LookupError(f"Review flag {review_flag_id} was not found.")
    return dict(row)


def create_review_action(
    *,
    review_flag_id: int,
    review_session_id: int | None,
    action_type: str,
    reviewer: str,
    note: str | None,
    original_value: str | None,
    modified_value: str | None,
    database_path: Path | None = None,
) -> dict[str, object]:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO review_actions (
                review_flag_id,
                review_session_id,
                action_type,
                reviewer,
                note,
                original_value,
                modified_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_flag_id,
                review_session_id,
                action_type,
                reviewer,
                note,
                original_value,
                modified_value,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM review_actions WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)
