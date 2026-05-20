from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.database.connection import open_connection
from backend.database.init_db import (
    REQUIRED_TABLES,
    get_initialized_tables,
    initialize_database,
    load_schema,
)


class DatabaseInitializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "depo_pro_test.db"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_database_initializes_and_creates_required_tables(self) -> None:
        initialize_database(self.database_path)
        self.assertTrue(self.database_path.exists())
        self.assertTrue(REQUIRED_TABLES.issubset(get_initialized_tables(self.database_path)))

    def test_schema_executes_cleanly(self) -> None:
        with open_connection(self.database_path) as connection:
            connection.executescript(load_schema())
            connection.commit()
        self.assertTrue(REQUIRED_TABLES.issubset(get_initialized_tables(self.database_path)))
