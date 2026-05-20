from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.database.init_db import initialize_database
from backend.database.models.case_models import CaseCreate
from backend.database.repositories.cases_repo import create_case, get_case, list_cases


class CaseRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "cases.db"
        initialize_database(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_get_case(self) -> None:
        created = create_case(
            CaseCreate(
                case_name="Anderson v. Metro Transit",
                caption="Anderson v. Metro Transit",
                cause_number="24-DC-1188",
                venue="Dallas County",
                jurisdiction="Texas",
            ),
            self.database_path,
        )
        fetched = get_case(created.id, self.database_path)
        self.assertEqual(fetched.case_name, "Anderson v. Metro Transit")
        self.assertEqual(fetched.cause_number, "24-DC-1188")

    def test_list_cases_returns_recent_records(self) -> None:
        create_case(CaseCreate(case_name="First Case"), self.database_path)
        create_case(CaseCreate(case_name="Second Case"), self.database_path)
        cases = list_cases(self.database_path)
        self.assertEqual(len(cases), 2)
        self.assertEqual(cases[0].case_name, "Second Case")
