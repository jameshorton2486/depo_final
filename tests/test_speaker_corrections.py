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
from backend.review.confidence_queue import ensure_review_queue
from backend.review.correction_engine import resolve_review_action
from backend.review.review_state import ReviewResolveRequest
from backend.review.transcript_query_service import get_review_timeline
from backend.transcript.transcript_service import TranscriptionRequest, transcribe_and_persist


def _make_audio(path: Path) -> Path:
    sample_rate = 16000
    timeline = np.arange(sample_rate * 8) / sample_rate
    samples = (0.16 * np.sin(2 * math.pi * 215 * timeline)).astype(np.float32)
    samples[:sample_rate] = 0.0
    sf.write(str(path), samples, sample_rate)
    return path


class SpeakerCorrectionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "phase6_speaker.db"
        self.data_root = self.root / "data"
        initialize_database(self.database_path)
        self.case_record = create_case(CaseCreate(case_name="Phase 6 Speaker"), self.database_path)
        self.session_record = create_session(
            SessionCreate(case_id=self.case_record.id, session_name="Session 1"),
            self.database_path,
        )
        self.audio_path = _make_audio(self.root / "phase6_speaker.wav")
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

    def test_speaker_reassignment_is_tracked_and_applied_to_review_timeline(self) -> None:
        queue = ensure_review_queue(self.session_record.id, self.database_path)
        speaker_item = next(item for item in queue if item["speaker_segment_id"] is not None)

        resolve_review_action(
            ReviewResolveRequest(
                session_id=self.session_record.id,
                review_flag_id=int(speaker_item["id"]),
                action="resolve",
                reviewer="Phase 6 Tester",
                corrected_speaker_label="MS. FLORA",
                corrected_role="attorney",
                note="Corrected diarized speaker label.",
            ),
            self.database_path,
        )
        timeline = get_review_timeline(self.session_record.id, self.database_path)

        self.assertEqual(timeline["timeline"][0]["speaker_label"], "MS. FLORA")
        self.assertEqual(timeline["timeline"][0]["speaker_role"], "attorney")
