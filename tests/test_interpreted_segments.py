from __future__ import annotations

import unittest

from backend.legal_review.interpreted_transcript import ensure_interpreted_segments
from backend.legal_review.review_dashboard import get_review_dashboard
from tests.legal_review_fixture import add_interpreter_block, build_transcribed_session


class InterpretedSegmentsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = build_transcribed_session("phase9_interpreted")
        add_interpreter_block(
            self.fixture["session_record"].id,
            self.fixture["database_path"],
        )

    def tearDown(self) -> None:
        self.fixture["temp_dir"].cleanup()

    def test_interpreted_segments_are_grouped_and_listed(self) -> None:
        items = ensure_interpreted_segments(
            self.fixture["session_record"].id,
            self.fixture["database_path"],
        )
        dashboard = get_review_dashboard(
            self.fixture["session_record"].id,
            self.fixture["database_path"],
        )

        self.assertTrue(items)
        self.assertEqual(dashboard["counts"]["interpreted_segments"], 1)
