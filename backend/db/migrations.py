"""Hand-rolled SQLite migrations for Depo-Pro.

Why hand-rolled instead of Alembic: this is a local-first single-user
desktop app. Hand-rolled migrations are easier to audit, ship with no
extra dependencies, and don't require a migration metadata table beyond
the schema_version table we own.

Migration files live next to this module as schema_v{N}.sql. Each
migration is idempotent - re-running apply() on an up-to-date database
is a no-op.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from loguru import logger

from backend import config

DB_PATH = config.DATA_ROOT / "depo_pro.sqlite3"
MIGRATIONS_DIR = Path(__file__).parent


def _connect() -> sqlite3.Connection:
    """Open a connection with foreign keys enabled."""
    config.DATA_ROOT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def current_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied schema version, or 0 if none."""
    try:
        row = conn.execute(
            "SELECT MAX(version) FROM schema_version"
        ).fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except sqlite3.OperationalError:
        return 0


def apply() -> int:
    """Apply all pending migrations. Returns the final schema version."""
    conn = _connect()
    try:
        version_before = current_version(conn)
        logger.info(f"DB schema version before apply: {version_before}")

        for sql_file in sorted(MIGRATIONS_DIR.glob("schema_v*.sql")):
            sql = sql_file.read_text(encoding="utf-8")
            logger.info(f"Applying {sql_file.name}")
            conn.executescript(sql)
            conn.commit()

        cols = [r[1] for r in conn.execute("PRAGMA table_info(case_attorneys)").fetchall()]
        if cols and "speaker_label" not in cols:
            logger.info("Adding missing speaker_label column to case_attorneys")
            conn.execute("ALTER TABLE case_attorneys ADD COLUMN speaker_label TEXT")
            conn.commit()

        version_after = current_version(conn)
        logger.info(f"DB schema version after apply: {version_after}")
        return version_after
    finally:
        conn.close()


def list_tables() -> list[str]:
    """Return all user tables (excluding sqlite_* internal tables)."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()
