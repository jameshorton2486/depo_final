from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from backend.database.init_db import initialize_database
from backend.database.models.case_models import CaseCreate
from backend.database.models.session_models import SessionCreate
from backend.database.repositories.cases_repo import create_case
from backend.database.repositories.sessions_repo import create_session
from backend.realtime.realtime_service import RealtimeSessionManager, RealtimeStartRequest
from backend.transcript.transcript_service import get_transcript


class RealtimePersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "phase8_persist.db"
        self.data_root = self.root / "data"
        initialize_database(self.database_path)
        self.case_record = create_case(CaseCreate(case_name="Phase 8 Persist"), self.database_path)
        self.session_record = create_session(
            SessionCreate(case_id=self.case_record.id, session_name="Live Session"),
            self.database_path,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_realtime_stream_persists_canonical_transcript_blocks(self) -> None:
        manager = RealtimeSessionManager(database_path=self.database_path, data_root=self.data_root)

        async def runner() -> None:
            await manager.start_session(
                RealtimeStartRequest(session_id=self.session_record.id, mock=True)
            )
            for _ in range(40):
                if manager.get_status(self.session_record.id)["completed"]:
                    return
                await asyncio.sleep(0.05)

        asyncio.run(runner())
        payload = get_transcript(self.session_record.id, self.database_path)

        self.assertGreaterEqual(len(payload["assets"]), 1)
        self.assertGreaterEqual(len(payload["transcript_blocks"]), 3)
        self.assertGreaterEqual(len(payload["word_objects"]), 3)
