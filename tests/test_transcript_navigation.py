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


class TranscriptNavigationTests(unittest.TestCase):
    def test_navigation_search_time_and_speaker_jumps(self) -> None:
        script = """
            const navigation = require('./frontend/assets/js/transcript/transcript_navigation.js');
            const blocks = [
                {
                    id: 1,
                    speaker_label: 'MR. YANG',
                    raw_text: 'Please state your name.',
                    search_text: 'mr. yang please state your name',
                    start_time: 0.0,
                    end_time: 2.0
                },
                {
                    id: 2,
                    speaker_label: 'THE WITNESS',
                    raw_text: 'Heath Thomas.',
                    search_text: 'the witness heath thomas',
                    start_time: 2.1,
                    end_time: 3.0
                }
            ];
            const filtered = navigation.filterBlocks(blocks, 'heath');
            const bySpeaker = navigation.jumpToSpeaker(blocks, 'MR. YANG');
            const byTime = navigation.jumpToTime(blocks, 2.5);
            const neighbor = navigation.neighborBlock(blocks, 1, 1);
            console.log(JSON.stringify({
                filteredCount: filtered.length,
                bySpeaker: bySpeaker ? bySpeaker.id : null,
                byTime: byTime ? byTime.id : null,
                neighbor: neighbor ? neighbor.id : null
            }));
        """
        payload = _run_node(script)

        self.assertEqual(payload["filteredCount"], 1)
        self.assertEqual(payload["bySpeaker"], 1)
        self.assertEqual(payload["byTime"], 2)
        self.assertEqual(payload["neighbor"], 2)
