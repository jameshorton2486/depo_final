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
from backend.transcript.transcript_service import (
    TranscriptionRequest,
    get_transcript,
    transcribe_and_persist,
)


def _make_audio(path: Path) -> Path:
    sample_rate = 16000
    timeline = np.arange(sample_rate * 8) / sample_rate
    samples = (0.22 * np.sin(2 * math.pi * 190 * timeline)).astype(np.float32)
    samples[:sample_rate] = 0.0
    sf.write(str(path), samples, sample_rate)
    return path


class TranscriptPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "phase4.db"
        self.data_root = self.root / "data"
        initialize_database(self.database_path)
        self.case_record = create_case(CaseCreate(case_name="Phase 4 Matter"), self.database_path)
        self.session_record = create_session(
            SessionCreate(case_id=self.case_record.id, session_name="Session 1"),
            self.database_path,
        )
        self.audio_path = _make_audio(self.root / "phase4.wav")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_prerecorded_pipeline_persists_raw_and_layer3_transcript(self) -> None:
        result = transcribe_and_persist(
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
        bundle = get_transcript(self.session_record.id, self.database_path)

        self.assertEqual(result["session_id"], self.session_record.id)
        self.assertTrue(Path(result["asset"]["deepgram_json_path"]).exists())
        self.assertGreaterEqual(result["transcript_summary"]["block_count"], 1)
        self.assertEqual(len(bundle["assets"]), 1)
        self.assertGreaterEqual(len(bundle["transcript_blocks"]), 1)
        self.assertGreaterEqual(len(bundle["word_objects"]), 1)
