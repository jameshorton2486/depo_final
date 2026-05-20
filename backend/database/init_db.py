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
}


def load_schema() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def initialize_database(database_path: Path | None = None) -> Path:
    resolved_path = resolve_database_path(database_path)
    with open_connection(resolved_path) as connection:
        connection.executescript(load_schema())
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
