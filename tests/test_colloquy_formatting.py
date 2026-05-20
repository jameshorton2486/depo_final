from __future__ import annotations

import unittest

from backend.database.models.transcript_models import BlockType, TranscriptTimelineBlock
from backend.export.colloquy_formatter import format_colloquy_block


class ColloquyFormattingTests(unittest.TestCase):
    def test_colloquy_block_renders_speaker_label_prefix(self) -> None:
        block = TranscriptTimelineBlock(
            id=2,
            session_id=1,
            block_index=2,
            block_type=BlockType.COLLOQUY,
            speaker_index=1,
            speaker_label="MS. FLORA",
            raw_text="Please mark Exhibit 4.",
            working_text=None,
            start_time=1.0,
            end_time=2.0,
            confidence=0.97,
            is_edited=False,
            words=[],
        )

        paragraph = format_colloquy_block(block)

        self.assertEqual(paragraph["prefix"], "MS. FLORA:")
        self.assertEqual(paragraph["runs"], ["MS. FLORA:", "\t", "Please mark Exhibit 4."])
