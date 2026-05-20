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
                case_style,
                cause_number,
                venue,
                jurisdiction,
                district_division,
                county,
                court_type,
                state,
                case_status,
                reporting_firm_id,
                reporting_firm_office_id,
                source_document,
                extracted_from,
                parser_confidence,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                payload.case_name,
                payload.caption,
                payload.case_style,
                payload.cause_number,
                payload.venue,
                payload.jurisdiction,
                payload.district_division,
                payload.county,
                payload.court_type,
                payload.state,
                payload.case_status,
                payload.reporting_firm_id,
                payload.reporting_firm_office_id,
                payload.source_document,
                payload.extracted_from,
                payload.parser_confidence,
            ),
        )
        connection.commit()
        return get_case(cursor.lastrowid, database_path)


def get_case(case_id: int, database_path: Path | None = None) -> CaseRecord:
    with open_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                id,
                case_name,
                caption,
                case_style,
                cause_number,
                venue,
                jurisdiction,
                district_division,
                county,
                court_type,
                state,
                case_status,
                reporting_firm_id,
                reporting_firm_office_id,
                source_document,
                extracted_from,
                parser_confidence,
                created_at,
                COALESCE(updated_at, created_at) AS updated_at
            FROM cases
            WHERE id = ?
            """,
            (case_id,),
        ).fetchone()
    if row is None:
        raise LookupError(f"Case {case_id} was not found.")
    return CaseRecord.model_validate(dict(row))


def list_cases(database_path: Path | None = None) -> list[CaseRecord]:
    with open_connection(database_path) as connection:
        rows = connection.execute("""
            SELECT
                id,
                case_name,
                caption,
                case_style,
                cause_number,
                venue,
                jurisdiction,
                district_division,
                county,
                court_type,
                state,
                case_status,
                reporting_firm_id,
                reporting_firm_office_id,
                source_document,
                extracted_from,
                parser_confidence,
                created_at,
                COALESCE(updated_at, created_at) AS updated_at
            FROM cases
            ORDER BY created_at DESC, id DESC
            """).fetchall()
    return [CaseRecord.model_validate(dict(row)) for row in rows]


def update_case(
    case_id: int, values: dict[str, object | None], database_path: Path | None = None
) -> CaseRecord:
    if not values:
        return get_case(case_id, database_path)
    columns = ", ".join(f"{column} = ?" for column in values)
    params = [*values.values(), case_id]
    with open_connection(database_path) as connection:
        connection.execute(
            f"UPDATE cases SET {columns}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            params,
        )
        connection.commit()
    return get_case(case_id, database_path)


def upsert_law_firm(
    name: str,
    *,
    address_line_1: str | None = None,
    address_line_2: str | None = None,
    city: str | None = None,
    state: str | None = None,
    postal_code: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    source_document: str | None = None,
    extracted_from: str | None = None,
    parser_confidence: float | None = None,
    database_path: Path | None = None,
) -> dict[str, object]:
    with open_connection(database_path) as connection:
        row = connection.execute("SELECT * FROM law_firms WHERE name = ?", (name,)).fetchone()
        if row is None:
            cursor = connection.execute(
                """
                INSERT INTO law_firms (
                    name, address_line_1, address_line_2, city, state, postal_code, phone, email,
                    source_document, extracted_from, parser_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    address_line_1,
                    address_line_2,
                    city,
                    state,
                    postal_code,
                    phone,
                    email,
                    source_document,
                    extracted_from,
                    parser_confidence,
                ),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM law_firms WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        else:
            connection.execute(
                """
                UPDATE law_firms
                SET address_line_1 = COALESCE(?, address_line_1),
                    address_line_2 = COALESCE(?, address_line_2),
                    city = COALESCE(?, city),
                    state = COALESCE(?, state),
                    postal_code = COALESCE(?, postal_code),
                    phone = COALESCE(?, phone),
                    email = COALESCE(?, email),
                    source_document = COALESCE(?, source_document),
                    extracted_from = COALESCE(?, extracted_from),
                    parser_confidence = COALESCE(?, parser_confidence)
                WHERE id = ?
                """,
                (
                    address_line_1,
                    address_line_2,
                    city,
                    state,
                    postal_code,
                    phone,
                    email,
                    source_document,
                    extracted_from,
                    parser_confidence,
                    row["id"],
                ),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM law_firms WHERE id = ?", (row["id"],)
            ).fetchone()
    return dict(row)


def replace_case_parties(
    case_id: int, parties: list[dict[str, object | None]], database_path: Path | None = None
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        connection.execute("DELETE FROM parties WHERE case_id = ?", (case_id,))
        created: list[dict[str, object]] = []
        for party in parties:
            cursor = connection.execute(
                """
                INSERT INTO parties (
                    case_id, party_name, party_type, side, role_modifier, alias_name,
                    entity_type, related_party_name, source_document, extracted_from,
                    parser_confidence, manual_override
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case_id,
                    party.get("party_name"),
                    party.get("party_type"),
                    party.get("side"),
                    party.get("role_modifier"),
                    party.get("alias_name"),
                    party.get("entity_type"),
                    party.get("related_party_name"),
                    party.get("source_document"),
                    party.get("extracted_from"),
                    party.get("parser_confidence"),
                    int(bool(party.get("manual_override"))),
                ),
            )
            created.append(
                dict(
                    connection.execute(
                        "SELECT * FROM parties WHERE id = ?", (cursor.lastrowid,)
                    ).fetchone()
                )
            )
        connection.commit()
    return created


def replace_case_attorneys(
    case_id: int,
    attorneys: list[dict[str, object | None]],
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        prior_ids = [
            row["attorney_id"]
            for row in connection.execute(
                "SELECT attorney_id FROM case_attorneys WHERE case_id = ?",
                (case_id,),
            ).fetchall()
        ]
        connection.execute("DELETE FROM case_attorneys WHERE case_id = ?", (case_id,))
        if prior_ids:
            placeholders = ", ".join("?" for _ in prior_ids)
            connection.execute(
                f"DELETE FROM attorneys WHERE id IN ({placeholders})",
                prior_ids,
            )
        connection.commit()

    created: list[dict[str, object]] = []
    with open_connection(database_path) as connection:
        for attorney in attorneys:
            law_firm_id = None
            firm_name = attorney.get("law_firm")
            if firm_name:
                law_firm = upsert_law_firm(
                    str(firm_name),
                    address_line_1=attorney.get("address_line_1"),
                    address_line_2=attorney.get("address_line_2"),
                    city=attorney.get("city"),
                    state=attorney.get("state"),
                    postal_code=attorney.get("postal_code"),
                    phone=attorney.get("phone"),
                    email=attorney.get("email"),
                    source_document=attorney.get("source_document"),
                    extracted_from=attorney.get("extracted_from"),
                    parser_confidence=attorney.get("parser_confidence"),
                    database_path=database_path,
                )
                law_firm_id = int(law_firm["id"])

            attorney_cursor = connection.execute(
                """
                INSERT INTO attorneys (
                    law_firm_id, full_name, email, phone, bar_number, bar_state,
                    address_line_1, address_line_2, city, state, postal_code, fax,
                    represented_party, source_document, extracted_from,
                    parser_confidence, manual_override
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    law_firm_id,
                    attorney.get("full_name"),
                    attorney.get("email"),
                    attorney.get("phone"),
                    attorney.get("bar_number"),
                    attorney.get("bar_state"),
                    attorney.get("address_line_1"),
                    attorney.get("address_line_2"),
                    attorney.get("city"),
                    attorney.get("state"),
                    attorney.get("postal_code"),
                    attorney.get("fax"),
                    attorney.get("represented_party"),
                    attorney.get("source_document"),
                    attorney.get("extracted_from"),
                    attorney.get("parser_confidence"),
                    int(bool(attorney.get("manual_override"))),
                ),
            )
            attorney_id = attorney_cursor.lastrowid
            party_row = connection.execute(
                """
                SELECT id
                FROM parties
                WHERE case_id = ?
                  AND (
                    party_name = ?
                    OR LOWER(side) = LOWER(?)
                    OR LOWER(party_type) = LOWER(?)
                  )
                ORDER BY id ASC
                LIMIT 1
                """,
                (
                    case_id,
                    attorney.get("represented_party"),
                    attorney.get("represented_party"),
                    attorney.get("represented_party"),
                ),
            ).fetchone()
            party_id = party_row["id"] if party_row else None
            case_attorney_cursor = connection.execute(
                """
                INSERT INTO case_attorneys (
                    case_id, attorney_id, party_id, role, speaker_label, represented_party_name,
                    is_lead, source_document, extracted_from, parser_confidence, manual_override
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case_id,
                    attorney_id,
                    party_id,
                    attorney.get("role"),
                    attorney.get("speaker_label"),
                    attorney.get("represented_party"),
                    int(bool(attorney.get("is_lead"))),
                    attorney.get("source_document"),
                    attorney.get("extracted_from"),
                    attorney.get("parser_confidence"),
                    int(bool(attorney.get("manual_override"))),
                ),
            )
            created.append(
                {
                    "attorney": dict(
                        connection.execute(
                            "SELECT * FROM attorneys WHERE id = ?", (attorney_id,)
                        ).fetchone()
                    ),
                    "case_attorney": dict(
                        connection.execute(
                            "SELECT * FROM case_attorneys WHERE id = ?",
                            (case_attorney_cursor.lastrowid,),
                        ).fetchone()
                    ),
                }
            )
        connection.commit()
    return created


def get_case_intake(case_id: int, database_path: Path | None = None) -> dict[str, object]:
    with open_connection(database_path) as connection:
        case_row = connection.execute(
            """
            SELECT
                id,
                case_name,
                caption,
                case_style,
                cause_number,
                venue,
                jurisdiction,
                district_division,
                county,
                court_type,
                state,
                case_status,
                reporting_firm_id,
                reporting_firm_office_id,
                source_document,
                extracted_from,
                parser_confidence,
                created_at,
                COALESCE(updated_at, created_at) AS updated_at
            FROM cases
            WHERE id = ?
            """,
            (case_id,),
        ).fetchone()
        if case_row is None:
            raise LookupError(f"Case {case_id} was not found.")
        parties = [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM parties WHERE case_id = ? ORDER BY id ASC", (case_id,)
            ).fetchall()
        ]
        attorneys = [
            {
                "attorney": dict(row),
                "case_attorney": dict(case_attorney),
            }
            for row, case_attorney in [
                (
                    connection.execute(
                        "SELECT * FROM attorneys WHERE id = ?", (pair["attorney_id"],)
                    ).fetchone(),
                    pair,
                )
                for pair in connection.execute(
                    "SELECT * FROM case_attorneys WHERE case_id = ? ORDER BY id ASC",
                    (case_id,),
                ).fetchall()
            ]
        ]
    return {"case": dict(case_row), "parties": parties, "attorneys": attorneys}
