from __future__ import annotations

import unittest

from backend.database.models.transcript_models import BlockType, TranscriptTimelineBlock
from backend.export.qa_formatter import format_qa_block


class QaFormattingTests(unittest.TestCase):
    def test_question_block_uses_tab_and_hanging_indent(self) -> None:
        block = TranscriptTimelineBlock(
            id=1,
            session_id=1,
            block_index=1,
            block_type=BlockType.EXAMINATION_Q,
            speaker_index=0,
            speaker_label="MR. YANG",
            raw_text="Did you inspect the systems?",
            working_text=None,
            start_time=0.0,
            end_time=1.0,
            confidence=0.99,
            is_edited=False,
            words=[],
        )

        paragraph = format_qa_block(block)

        self.assertEqual(paragraph["prefix"], "Q.")
        self.assertEqual(paragraph["runs"], ["Q.", "\t", "Did you inspect the systems?"])
        self.assertGreater(paragraph["left_twips"], 0)
        self.assertGreater(paragraph["hanging_twips"], 0)
