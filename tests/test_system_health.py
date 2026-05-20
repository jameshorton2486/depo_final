from __future__ import annotations

import unittest

from legal_review_fixture import build_transcribed_session

from backend.system.health_monitor import get_system_health
from backend.system.startup_validation import run_startup_validation


class SystemHealthTests(unittest.TestCase):
    def test_startup_validation_and_system_health_pass_for_transcribed_session(self) -> None:
        fixture = build_transcribed_session("phase10_health")
        self.addCleanup(fixture["temp_dir"].cleanup)

        startup = run_startup_validation(fixture["database_path"])
        health = get_system_health(fixture["database_path"])

        self.assertTrue(startup["ok"])
        self.assertIn(health["status"], {"ok", "warning"})
        self.assertTrue(health["startup_valid"])
