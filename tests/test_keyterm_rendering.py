from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_entity_extraction import SAMPLE_TEXT

from backend.database.init_db import initialize_database
from backend.services.intake_service import IntakeParseRequest, get_intake, parse_and_persist


class KeytermRenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "phasea_keyterms.db"
        initialize_database(self.database_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_keyterm_payload_contains_render_metadata(self) -> None:
        result = parse_and_persist(
            IntakeParseRequest(
                pasted_text=SAMPLE_TEXT,
                intake_metadata={"source_document": "keyterms.txt"},
            ),
            self.database_path,
        )
        payload = get_intake(result["case_id"], self.database_path)

        self.assertIn("generated_at", payload["keyterms"])
        self.assertTrue(payload["keyterms"]["keyterms"])
        term = payload["keyterms"]["keyterms"][0]
        self.assertIn("category", term)
        self.assertIn("weight", term)
        self.assertIn("source", term)
