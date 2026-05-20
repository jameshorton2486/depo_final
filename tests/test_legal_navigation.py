from __future__ import annotations

import unittest

from backend.legal_review.legal_navigation import get_navigation_index
from backend.legal_review.review_dashboard import get_review_dashboard
from backend.legal_review.transcript_annotations import AnnotationCreate, create_annotation
from backend.review.transcript_query_service import get_review_timeline
from tests.legal_review_fixture import build_transcribed_session


class LegalNavigationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_transcribed_session("phase9_navigation")

    def tearDown(self) -> None:
        self.fixture["temp_dir"].cleanup()

    def test_bookmark_annotation_persists_and_appears_in_navigation(self) -> None:
        timeline = get_review_timeline(
            self.fixture["session_record"].id,
            self.fixture["database_path"],
        )
        block_id = int(timeline["timeline"][0]["id"])
        annotation = create_annotation(
            AnnotationCreate(
                session_id=self.fixture["session_record"].id,
                transcript_block_id=block_id,
                annotation_type="BOOKMARK",
                annotation_text="Key witness admission",
                bookmark_label="Admission",
                issue_category="UNRESOLVED_ENTITY",
                author="Phase 9 Tester",
            ),
            self.fixture["database_path"],
        )
        navigation = get_navigation_index(
            self.fixture["session_record"].id,
            self.fixture["database_path"],
        )
        dashboard = get_review_dashboard(
            self.fixture["session_record"].id,
            self.fixture["database_path"],
        )

        self.assertEqual(annotation["bookmark_label"], "Admission")
        self.assertTrue(any(item["nav_type"] == "BOOKMARK" for item in navigation["items"]))
        self.assertTrue(dashboard["annotations"])
