from __future__ import annotations

import unittest

from legal_review_fixture import build_transcribed_session

from backend.database.connection import open_connection
from backend.database.models.transcript_models import (
    BlockType,
    SpeakerSegmentCreate,
    TranscriptBlockCreate,
)
from backend.database.repositories.transcript_repo import (
    create_speaker_segment,
    create_transcript_block,
)
from backend.system.transcript_integrity import check_session_integrity


class TranscriptIntegrityTests(unittest.TestCase):
    def test_integrity_passes_for_mock_transcript(self) -> None:
        fixture = build_transcribed_session("phase10_integrity_ok")
        self.addCleanup(fixture["temp_dir"].cleanup)

        report = check_session_integrity(fixture["session_record"].id, fixture["database_path"])

        self.assertTrue(report["ok"])
        self.assertEqual(report["issue_count"], 0)

    def test_integrity_detects_overlapping_block_corruption(self) -> None:
        fixture = build_transcribed_session("phase10_integrity_bad")
        self.addCleanup(fixture["temp_dir"].cleanup)
        session_id = fixture["session_record"].id
        database_path = fixture["database_path"]

        speaker = create_speaker_segment(
            SpeakerSegmentCreate(
                session_id=session_id,
                speaker_index=15,
                speaker_label="MR. TEST",
                start_time=1.0,
                end_time=1.4,
                confidence=0.9,
            ),
            database_path,
        )
        create_transcript_block(
            TranscriptBlockCreate(
                session_id=session_id,
                speaker_segment_id=speaker.id,
                block_index=500,
                block_type=BlockType.COLLOQUY,
                speaker_index=15,
                raw_text="Injected overlapping block.",
                working_text=None,
                start_time=1.0,
                end_time=1.4,
                confidence=0.9,
                is_edited=False,
            ),
            database_path,
        )
        with open_connection(database_path) as connection:
            connection.execute("""
                UPDATE word_objects
                SET confidence = 1.5
                WHERE id = (SELECT id FROM word_objects LIMIT 1)
                """)
            connection.commit()

        report = check_session_integrity(session_id, database_path)

        self.assertFalse(report["ok"])
        self.assertGreaterEqual(report["issue_count"], 1)
        self.assertTrue(any(item["code"] == "OVERLAPPING_BLOCKS" for item in report["issues"]))
