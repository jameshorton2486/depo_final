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


class ZoomRtmsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "phase8_zoom.db"
        self.data_root = self.root / "data"
        initialize_database(self.database_path)
        self.case_record = create_case(CaseCreate(case_name="Phase 8 Zoom"), self.database_path)
        self.session_record = create_session(
            SessionCreate(case_id=self.case_record.id, session_name="Live Session"),
            self.database_path,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_start_session_reports_zoom_metadata_and_completes(self) -> None:
        manager = RealtimeSessionManager(database_path=self.database_path, data_root=self.data_root)

        async def runner() -> dict[str, object]:
            await manager.start_session(
                RealtimeStartRequest(
                    session_id=self.session_record.id,
                    meeting_id="987654321",
                    passcode="abc123",
                    mock=True,
                )
            )
            for _ in range(40):
                status = manager.get_status(self.session_record.id)
                if status["completed"]:
                    return status
                await asyncio.sleep(0.05)
            return manager.get_status(self.session_record.id)

        status = asyncio.run(runner())

        self.assertTrue(status["mock"])
        self.assertTrue(status["metadata"]["passcode_present"])
        self.assertEqual(status["metadata"]["meeting_id"], "987654321")
        self.assertTrue(status["completed"])
