from __future__ import annotations

import unittest

from backend.legal_review.objection_service import ObjectionCreate, create_objection
from backend.legal_review.review_dashboard import get_review_dashboard
from backend.review.transcript_query_service import get_review_timeline
from tests.legal_review_fixture import build_transcribed_session


class ObjectionWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_transcribed_session("phase9_objection")

    def tearDown(self) -> None:
        self.fixture["temp_dir"].cleanup()

    def test_objection_persists_and_creates_issue(self) -> None:
        timeline = get_review_timeline(
            self.fixture["session_record"].id,
            self.fixture["database_path"],
        )
        block_id = int(timeline["timeline"][0]["id"])

        result = create_objection(
            ObjectionCreate(
                session_id=self.fixture["session_record"].id,
                transcript_block_id=block_id,
                category="FORM",
                objection_text="Objection, form.",
                reviewer="Phase 9 Tester",
            ),
            self.fixture["database_path"],
        )
        dashboard = get_review_dashboard(
            self.fixture["session_record"].id,
            self.fixture["database_path"],
        )

        self.assertEqual(result["objection"]["category"], "FORM")
        self.assertTrue(dashboard["objections"])
        self.assertTrue(dashboard["issues"])
