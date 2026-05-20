from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection
from backend.database.models.case_models import CaseCreate, CaseRecord


def create_case(payload: CaseCreate, database_path: Path | None = None) -> CaseRecord:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO cases (
                case_name,
                caption,
                cause_number,
                venue,
                jurisdiction,
                case_status,
                reporting_firm_id,
                reporting_firm_office_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.case_name,
                payload.caption,
                payload.cause_number,
                payload.venue,
                payload.jurisdiction,
                payload.case_status,
                payload.reporting_firm_id,
                payload.reporting_firm_office_id,
            ),
        )
        connection.commit()
        return get_case(cursor.lastrowid, database_path)


def get_case(case_id: int, database_path: Path | None = None) -> CaseRecord:
    with open_connection(database_path) as connection:
        row = connection.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    if row is None:
        raise LookupError(f"Case {case_id} was not found.")
    return CaseRecord.model_validate(dict(row))


def list_cases(database_path: Path | None = None) -> list[CaseRecord]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM cases ORDER BY created_at DESC, id DESC"
        ).fetchall()
    return [CaseRecord.model_validate(dict(row)) for row in rows]
