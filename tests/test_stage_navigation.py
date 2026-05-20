from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_entity_extraction import SAMPLE_TEXT

from backend.database.init_db import initialize_database
from backend.services.intake_service import (
    IntakeParseRequest,
    list_intake_cases,
    parse_and_persist,
    update_case_stage,
)


class StageNavigationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "phasea_stage.db"
        initialize_database(self.database_path)
        self.result = parse_and_persist(
            IntakeParseRequest(
                pasted_text=SAMPLE_TEXT,
                intake_metadata={"source_document": "stage.txt"},
            ),
            self.database_path,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_stage_updates_are_persisted_in_case_listing(self) -> None:
        update_case_stage(self.result["case_id"], 4, self.database_path)

        listing = list_intake_cases(self.database_path)

        item = next(
            entry for entry in listing["items"] if entry["case"]["id"] == self.result["case_id"]
        )
        self.assertEqual(item["case_state"]["stage_id"], 4)
        self.assertEqual(item["case_state"]["stage_key"], "insertions")
