from __future__ import annotations

import unittest

from legal_review_fixture import build_transcribed_session

from backend.realtime.stream_persistence import log_session_event
from backend.system.performance_metrics import get_performance_metrics


class PerformanceMetricsTests(unittest.TestCase):
    def test_performance_metrics_include_session_rollup(self) -> None:
        fixture = build_transcribed_session("phase10_performance")
        self.addCleanup(fixture["temp_dir"].cleanup)
        session_id = fixture["session_record"].id
        database_path = fixture["database_path"]

        log_session_event(
            session_id,
            "realtime_started",
            event_time=0.0,
            details={"source": "test"},
            database_path=database_path,
        )

        payload = get_performance_metrics(session_id=session_id, database_path=database_path)

        self.assertEqual(payload["session_count"], 1)
        self.assertEqual(payload["sessions"][0]["session_id"], session_id)
        self.assertGreaterEqual(payload["sessions"][0]["word_count"], 1)
