from __future__ import annotations

import json
import subprocess
import unittest


def _run_node(script: str) -> dict[str, object]:
    process = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(process.stdout)


class ConfidenceMappingTests(unittest.TestCase):
    def test_confidence_thresholds_match_workspace_rules(self) -> None:
        script = """
            const confidence = require(
                './frontend/assets/js/transcript/confidence_highlighting.js'
            );
            console.log(JSON.stringify({
                high: confidence.classify(0.97),
                medium: confidence.classify(0.9),
                low: confidence.classify(0.7),
                candidate: confidence.isReviewCandidate(0.7),
            }));
        """
        payload = _run_node(script)

        self.assertEqual(payload["high"], "high")
        self.assertEqual(payload["medium"], "medium")
        self.assertEqual(payload["low"], "low")
        self.assertTrue(payload["candidate"])
