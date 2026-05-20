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


class PlaybackSyncTests(unittest.TestCase):
    def test_playback_sync_maps_time_to_active_word_and_seek(self) -> None:
        script = """
            const playback = require('./frontend/assets/js/transcript/playback_sync.js');
            const timeline = [
                { word_id: 10, block_id: 1, start_time: 0.0, end_time: 0.4 },
                { word_id: 11, block_id: 1, start_time: 0.41, end_time: 0.82 }
            ];
            const player = { currentTime: 0 };
            playback.seekPlayer(player, 0.5);
            const active = playback.activeState(timeline, 0.5);
            console.log(JSON.stringify({
                currentTime: player.currentTime,
                activeWordId: active.activeWordId,
                activeBlockId: active.activeBlockId
            }));
        """
        payload = _run_node(script)

        self.assertEqual(payload["currentTime"], 0.5)
        self.assertEqual(payload["activeWordId"], 11)
        self.assertEqual(payload["activeBlockId"], 1)
