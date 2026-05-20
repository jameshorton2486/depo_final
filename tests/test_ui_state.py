from __future__ import annotations

import unittest

from legal_review_fixture import build_transcribed_session

from backend.services.intake_service import get_intake, update_case_stage


class UiStateTests(unittest.TestCase):
    def test_intake_payload_exposes_ui_wiring_state(self) -> None:
        fixture = build_transcribed_session("phasea_ui_state")
        self.addCleanup(fixture["temp_dir"].cleanup)
        case_id = fixture["case_record"].id

        update_case_stage(case_id, 3, fixture["database_path"])
        payload = get_intake(case_id, fixture["database_path"])

        self.assertIn("speaker_labels", payload)
        self.assertIn("provenance_entries", payload)
        self.assertIn("case_state", payload)
        self.assertGreaterEqual(len(payload["speaker_labels"]), 2)
        self.assertEqual(payload["case_state"]["stage_id"], 3)
