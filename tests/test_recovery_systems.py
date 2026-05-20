from __future__ import annotations

import unittest
from pathlib import Path

from legal_review_fixture import build_transcribed_session

from backend.realtime.stream_persistence import log_session_event
from backend.system.recovery_manager import RecoveryRequest, run_recovery


class RecoverySystemTests(unittest.TestCase):
    def test_recovery_scan_and_checkpoint_work(self) -> None:
        fixture = build_transcribed_session("phase10_recovery")
        self.addCleanup(fixture["temp_dir"].cleanup)
        session_id = fixture["session_record"].id
        database_path = fixture["database_path"]
        data_root = fixture["data_root"]

        log_session_event(
            session_id,
            "realtime_started",
            event_time=0.0,
            details={"reason": "test"},
            database_path=database_path,
        )

        scan_result = run_recovery(
            RecoveryRequest(action="scan"),
            database_path=database_path,
            data_root=data_root,
        )
        checkpoint_result = run_recovery(
            RecoveryRequest(action="checkpoint", session_id=session_id),
            database_path=database_path,
            data_root=data_root,
        )

        self.assertIn("reconnect_candidates", scan_result["result"])
        self.assertTrue(Path(checkpoint_result["result"]["checkpoint_path"]).exists())
