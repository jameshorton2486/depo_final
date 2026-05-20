from __future__ import annotations

import unittest

from backend.legal_review.exhibit_service import ExhibitLinkCreate, create_exhibit_link
from backend.legal_review.legal_navigation import get_navigation_index
from backend.review.transcript_query_service import get_review_timeline
from tests.legal_review_fixture import build_transcribed_session


class ExhibitLinkingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_transcribed_session("phase9_exhibit")

    def tearDown(self) -> None:
        self.fixture["temp_dir"].cleanup()

    def test_exhibit_link_persists_and_indexes_navigation(self) -> None:
        timeline = get_review_timeline(
            self.fixture["session_record"].id,
            self.fixture["database_path"],
        )
        block_id = int(timeline["timeline"][0]["id"])

        result = create_exhibit_link(
            ExhibitLinkCreate(
                session_id=self.fixture["session_record"].id,
                transcript_block_id=block_id,
                exhibit_label="Exhibit 4",
                exhibit_description="Mechanical systems report",
                created_by="Phase 9 Tester",
            ),
            self.fixture["database_path"],
        )
        navigation = get_navigation_index(
            self.fixture["session_record"].id,
            self.fixture["database_path"],
        )

        self.assertEqual(result["linked_exhibit"]["exhibit_label"], "Exhibit 4")
        self.assertTrue(any(item["nav_type"] == "EXHIBIT" for item in navigation["items"]))
