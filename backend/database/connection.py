from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from backend.config import settings


def resolve_database_path(database_path: Path | None = None) -> Path:
    return database_path if database_path is not None else settings.database_path


def get_connection(database_path: Path | None = None) -> sqlite3.Connection:
    resolved_path = resolve_database_path(database_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(resolved_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


@contextmanager
def open_connection(database_path: Path | None = None):
    connection = get_connection(database_path)
    try:
        yield connection
    finally:
        connection.close()
