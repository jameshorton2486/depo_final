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
from backend.transcript.transcript_service import TranscriptionRequest, transcribe_and_persist


def _make_audio(path: Path) -> Path:
    sample_rate = 16000
    timeline = np.arange(sample_rate * 8) / sample_rate
    samples = (0.16 * np.sin(2 * math.pi * 210 * timeline)).astype(np.float32)
    samples[:sample_rate] = 0.0
    sf.write(str(path), samples, sample_rate)
    return path


class ReviewQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "phase6_queue.db"
        self.data_root = self.root / "data"
        initialize_database(self.database_path)
        self.case_record = create_case(CaseCreate(case_name="Phase 6 Queue"), self.database_path)
        self.session_record = create_session(
            SessionCreate(case_id=self.case_record.id, session_name="Session 1"),
            self.database_path,
        )
        self.audio_path = _make_audio(self.root / "phase6_queue.wav")
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

    def test_queue_populates_and_review_resolution_persists(self) -> None:
        items = ensure_review_queue(self.session_record.id, self.database_path)
        low_confidence_item = next(
            item for item in items if item["issue_category"] == "LOW_CONFIDENCE"
        )

        result = resolve_review_action(
            ReviewResolveRequest(
                session_id=self.session_record.id,
                review_flag_id=int(low_confidence_item["id"]),
                action="resolve",
                reviewer="Phase 6 Tester",
                note="Apply deterministic cleanup.",
                apply_deterministic_rules=True,
            ),
            self.database_path,
        )

        self.assertEqual(result["review_flag"]["status"], "reviewed")
        self.assertEqual(result["review_action"]["reviewer"], "Phase 6 Tester")
        self.assertEqual(result["audit_event"]["correction_source"], "deterministic_rule")
