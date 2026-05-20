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
                location_type,
                location_address,
                deponent_name,
                officer_name,
                ordered_by,
                service_type,
                csr_required,
                source_document,
                extracted_from,
                parser_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.case_id,
                payload.session_name,
                payload.session_date,
                payload.start_time,
                payload.end_time,
                payload.location,
                payload.location_type,
                payload.location_address,
                payload.deponent_name,
                payload.officer_name,
                payload.ordered_by,
                payload.service_type,
                int(payload.csr_required),
                payload.source_document,
                payload.extracted_from,
                payload.parser_confidence,
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


def list_sessions_for_case(case_id: int, database_path: Path | None = None) -> list[SessionRecord]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM sessions WHERE case_id = ? ORDER BY id ASC",
            (case_id,),
        ).fetchall()
    return [SessionRecord.model_validate(dict(row)) for row in rows]
