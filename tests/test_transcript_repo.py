from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from backend.database.init_db import initialize_database
from backend.database.models.case_models import CaseCreate
from backend.database.models.session_models import SessionCreate
from backend.database.models.transcript_models import (
    BlockType,
    TranscriptAssetCreate,
    TranscriptBlockCreate,
    WordObjectCreate,
)
from backend.database.repositories.assets_repo import (
    create_transcript_asset,
    get_assets_for_session,
)
from backend.database.repositories.cases_repo import create_case
from backend.database.repositories.sessions_repo import create_session
from backend.database.repositories.transcript_repo import (
    create_transcript_block,
    get_blocks_for_session,
    insert_word_object,
)


class TranscriptRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "transcript.db"
        initialize_database(self.database_path)
        self.case = create_case(CaseCreate(case_name="Transcript Matter"), self.database_path)
        self.session = create_session(
            SessionCreate(case_id=self.case.id, session_name="Session 1"),
            self.database_path,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_assets_blocks_and_words(self) -> None:
        asset = create_transcript_asset(
            TranscriptAssetCreate(
                session_id=self.session.id,
                asset_type="audio",
                file_name="session_1.wav",
                file_path="data/audio/session_1.wav",
                source_format="wav",
                deepgram_json_path="data/transcripts/session_1.deepgram.json",
                keyterms_path="data/transcripts/session_1.keyterms.json",
                preprocessing_metadata_path="data/temp/session_1.preprocess.json",
                snr_value=28.4,
                utt_split_value=0.75,
                is_primary=True,
            ),
            self.database_path,
        )
        block = create_transcript_block(
            TranscriptBlockCreate(
                session_id=self.session.id,
                block_index=1,
                block_type=BlockType.EXAMINATION_Q,
                speaker_index=1,
                raw_text="Please state your name for the record.",
                start_time=0.0,
                end_time=2.4,
                confidence=0.98,
            ),
            self.database_path,
        )
        word = insert_word_object(
            WordObjectCreate(
                transcript_block_id=block.id,
                word_index=1,
                word_text="Please",
                start_time=0.0,
                end_time=0.31,
                confidence=0.97,
                is_filler=False,
            ),
            self.database_path,
        )

        assets = get_assets_for_session(self.session.id, self.database_path)
        blocks = get_blocks_for_session(self.session.id, self.database_path)

        self.assertEqual(asset.session_id, self.session.id)
        self.assertEqual(word.transcript_block_id, block.id)
        self.assertEqual(len(assets), 1)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].block_type, BlockType.EXAMINATION_Q)

    def test_foreign_key_integrity_on_word_objects(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            insert_word_object(
                WordObjectCreate(
                    transcript_block_id=9999,
                    word_index=1,
                    word_text="test",
                    start_time=0.0,
                    end_time=0.1,
                ),
                self.database_path,
            )
