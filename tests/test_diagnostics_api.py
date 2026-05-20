from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.app import app


class DiagnosticsApiTests(unittest.TestCase):
    def test_diagnostics_endpoint_returns_summary_counts(self) -> None:
        client = TestClient(app)

        response = client.get("/api/system/diagnostics")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("summary", payload)
        self.assertIn("sessions_scanned", payload["summary"])
        self.assertIn("missing_asset_count", payload["summary"])
