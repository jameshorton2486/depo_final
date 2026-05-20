from __future__ import annotations

import unittest

from backend.realtime.live_transcript_buffer import LiveTranscriptBuffer


class LiveBufferTests(unittest.TestCase):
    def test_buffer_appends_blocks_and_supports_search(self) -> None:
        buffer = LiveTranscriptBuffer(session_id=44)
        buffer.add_block(
            {
                "id": 1,
                "speaker_label": "MR. YANG",
                "raw_text": "Please state your name.",
                "words": [
                    {
                        "id": 100,
                        "word_text": "Please",
                        "start_time": 0.0,
                        "end_time": 0.2,
                        "confidence": 0.98,
                    }
                ],
            },
            latency_ms=135,
        )

        snapshot = buffer.snapshot()

        self.assertEqual(snapshot["packet_count"], 1)
        self.assertEqual(snapshot["last_latency_ms"], 135)
        self.assertEqual(snapshot["speaker_labels"], ["MR. YANG"])
        self.assertEqual(len(buffer.search("name")), 1)
