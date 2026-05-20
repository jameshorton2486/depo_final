from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection
from backend.database.models.session_models import SessionCreate, SessionRecord


def create_session(payload: SessionCreate, database_path: Path | None = None) -> SessionRecord:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO sessions (
                case_id,
                session_name,
                session_date,
                start_time,
                end_time,
                location,
                deponent_name,
                officer_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.case_id,
                payload.session_name,
                payload.session_date,
                payload.start_time,
                payload.end_time,
                payload.location,
                payload.deponent_name,
                payload.officer_name,
            ),
        )
        connection.commit()
        return get_session(cursor.lastrowid, database_path)


def get_session(session_id: int, database_path: Path | None = None) -> SessionRecord:
    with open_connection(database_path) as connection:
        row = connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None:
        raise LookupError(f"Session {session_id} was not found.")
    return SessionRecord.model_validate(dict(row))
