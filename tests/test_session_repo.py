from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.database.init_db import initialize_database
from backend.database.models.case_models import CaseCreate
from backend.database.models.session_models import SessionCreate
from backend.database.repositories.cases_repo import create_case
from backend.database.repositories.sessions_repo import create_session, get_session


class SessionRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "sessions.db"
        initialize_database(self.database_path)
        self.case = create_case(CaseCreate(case_name="Deposition Matter"), self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_get_session(self) -> None:
        created = create_session(
            SessionCreate(
                case_id=self.case.id,
                session_name="Day 1 PM",
                session_date="2026-05-19",
                location="Dallas",
                deponent_name="Jamie Porter",
            ),
            self.database_path,
        )
        fetched = get_session(created.id, self.database_path)
        self.assertEqual(fetched.session_name, "Day 1 PM")
        self.assertEqual(fetched.case_id, self.case.id)

    def test_foreign_key_integrity_on_sessions(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            create_session(
                SessionCreate(case_id=9999, session_name="Invalid Session"),
                self.database_path,
            )
