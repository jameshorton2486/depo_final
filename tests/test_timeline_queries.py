from __future__ import annotations

import base64
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from backend.database.init_db import initialize_database
from backend.database.models.case_models import CaseCreate
from backend.database.models.session_models import SessionCreate
from backend.database.repositories.cases_repo import create_case
from backend.database.repositories.sessions_repo import create_session
from backend.review.transcript_query_service import get_review_timeline, get_review_word
from backend.transcript.transcript_service import TranscriptionRequest, transcribe_and_persist


def _make_audio(path: Path) -> Path:
    sample_rate = 16000
    timeline = np.arange(sample_rate * 8) / sample_rate
    samples = (0.18 * np.sin(2 * math.pi * 205 * timeline)).astype(np.float32)
    samples[:sample_rate] = 0.0
    sf.write(str(path), samples, sample_rate)
    return path


class TimelineQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "phase5.db"
        self.data_root = self.root / "data"
        initialize_database(self.database_path)
        self.case_record = create_case(CaseCreate(case_name="Phase 5 Matter"), self.database_path)
        self.session_record = create_session(
            SessionCreate(case_id=self.case_record.id, session_name="Session 1"),
            self.database_path,
        )
        self.audio_path = _make_audio(self.root / "phase5.wav")
        transcribe_and_persist(
            TranscriptionRequest(
                case_id=self.case_record.id,
                session_id=self.session_record.id,
                file_name=self.audio_path.name,
                file_content_base64=base64.b64encode(self.audio_path.read_bytes()).decode("utf-8"),
            ),
            database_path=self.database_path,
            data_root=self.data_root,
            mock=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_timeline_query_returns_ordered_blocks_and_playback_metadata(self) -> None:
        payload = get_review_timeline(self.session_record.id, self.database_path)

        self.assertEqual(payload["session_id"], self.session_record.id)
        self.assertTrue(payload["timeline"])
        self.assertEqual(payload["timeline"][0]["block_index"], 1)
        self.assertTrue(payload["playback"]["word_timeline"])
        self.assertEqual(
            payload["playback"]["media_url"],
            f"/api/transcript/{self.session_record.id}/media",
        )
        self.assertIn("high", payload["confidence_summary"])

    def test_review_word_returns_seek_metadata(self) -> None:
        timeline = get_review_timeline(self.session_record.id, self.database_path)
        word_id = timeline["timeline"][0]["words"][0]["id"]
        payload = get_review_word(self.session_record.id, word_id, self.database_path)

        self.assertEqual(payload["id"], word_id)
        self.assertEqual(payload["seek_time"], payload["start_time"])
        self.assertIn(payload["confidence_class"], {"high", "medium", "low"})
