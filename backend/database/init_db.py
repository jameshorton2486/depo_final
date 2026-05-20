from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection, resolve_database_path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
REQUIRED_TABLES = {
    "law_firms",
    "reporting_firms",
    "reporting_firm_offices",
    "cases",
    "parties",
    "attorneys",
    "case_attorneys",
    "sessions",
    "transcript_assets",
    "exhibits",
    "interpreters",
    "session_events",
    "speaker_segments",
    "transcript_blocks",
    "word_objects",
    "review_sessions",
    "review_flags",
    "review_actions",
    "speaker_corrections",
    "transcript_audit_log",
    "transcript_annotations",
    "objections",
    "review_issues",
    "linked_exhibits",
    "interpreted_segments",
    "legal_navigation_index",
}
REQUIRED_COLUMNS = {
    "law_firms": {
        "address_line_1": "TEXT",
        "address_line_2": "TEXT",
        "city": "TEXT",
        "state": "TEXT",
        "postal_code": "TEXT",
        "phone": "TEXT",
        "email": "TEXT",
        "source_document": "TEXT",
        "extracted_from": "TEXT",
        "parser_confidence": "REAL",
    },
    "cases": {
        "caption": "TEXT",
        "cause_number": "TEXT",
        "venue": "TEXT",
        "jurisdiction": "TEXT",
        "case_style": "TEXT",
        "district_division": "TEXT",
        "county": "TEXT",
        "court_type": "TEXT",
        "state": "TEXT",
        "case_status": "TEXT",
        "reporting_firm_id": "INTEGER",
        "reporting_firm_office_id": "INTEGER",
        "source_document": "TEXT",
        "extracted_from": "TEXT",
        "parser_confidence": "REAL",
        "updated_at": "TEXT",
    },
    "parties": {
        "role_modifier": "TEXT",
        "alias_name": "TEXT",
        "entity_type": "TEXT",
        "related_party_name": "TEXT",
        "source_document": "TEXT",
        "extracted_from": "TEXT",
        "parser_confidence": "REAL",
        "manual_override": "INTEGER NOT NULL DEFAULT 0",
    },
    "attorneys": {
        "bar_state": "TEXT",
        "address_line_1": "TEXT",
        "address_line_2": "TEXT",
        "city": "TEXT",
        "state": "TEXT",
        "postal_code": "TEXT",
        "fax": "TEXT",
        "represented_party": "TEXT",
        "source_document": "TEXT",
        "extracted_from": "TEXT",
        "parser_confidence": "REAL",
        "manual_override": "INTEGER NOT NULL DEFAULT 0",
    },
    "case_attorneys": {
        "represented_party_name": "TEXT",
        "is_lead": "INTEGER NOT NULL DEFAULT 0",
        "source_document": "TEXT",
        "extracted_from": "TEXT",
        "parser_confidence": "REAL",
        "manual_override": "INTEGER NOT NULL DEFAULT 0",
    },
    "sessions": {
        "start_time": "TEXT",
        "end_time": "TEXT",
        "location": "TEXT",
        "location_type": "TEXT",
        "location_address": "TEXT",
        "deponent_name": "TEXT",
        "officer_name": "TEXT",
        "ordered_by": "TEXT",
        "service_type": "TEXT",
        "csr_required": "INTEGER NOT NULL DEFAULT 0",
        "source_document": "TEXT",
        "extracted_from": "TEXT",
        "parser_confidence": "REAL",
    },
    "transcript_assets": {
        "source_format": "TEXT",
        "deepgram_json_path": "TEXT",
        "keyterms_path": "TEXT",
        "preprocessing_metadata_path": "TEXT",
        "snr_value": "REAL",
        "utt_split_value": "REAL",
        "is_primary": "INTEGER NOT NULL DEFAULT 0",
    },
}


def load_schema() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def initialize_database(database_path: Path | None = None) -> Path:
    resolved_path = resolve_database_path(database_path)
    with open_connection(resolved_path) as connection:
        connection.executescript(load_schema())
        _ensure_required_columns(connection)
        connection.commit()
    return resolved_path


def get_initialized_tables(database_path: Path | None = None) -> set[str]:
    with open_connection(database_path) as connection:
        rows = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """).fetchall()
    return {row["name"] for row in rows}


def database_status(database_path: Path | None = None) -> dict[str, bool | str]:
    initialize_database(database_path)
    tables = get_initialized_tables(database_path)
    return {
        "database": "connected",
        "tables_initialized": REQUIRED_TABLES.issubset(tables),
    }


def _ensure_required_columns(connection) -> None:
    for table_name, required_columns in REQUIRED_COLUMNS.items():
        existing = {
            row["name"] for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        for column_name, column_sql in required_columns.items():
            if column_name not in existing:
                connection.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
                )
