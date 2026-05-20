from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np
import soundfile as sf

from backend.deepgram.prerecorded import transcribe_prerecorded
from backend.deepgram.request_builder import build_prerecorded_request_url


def _make_audio(path: Path) -> Path:
    sample_rate = 16000
    samples = (0.3 * np.sin(2 * np.pi * 220 * np.arange(sample_rate * 4) / sample_rate)).astype(
        np.float32
    )
    sf.write(str(path), samples, sample_rate)
    return path


class DeepgramRequestTests(unittest.TestCase):
    def test_request_builder_uses_phase4_transcription_flags(self) -> None:
        url = build_prerecorded_request_url(utt_split=0.875, prompted_terms=["PeirsonPatterson"])
        params = parse_qs(urlparse(url).query)

        self.assertEqual(params["model"][0], "nova-3")
        self.assertEqual(params["punctuate"][0], "true")
        self.assertEqual(params["paragraphs"][0], "true")
        self.assertEqual(params["diarize"][0], "true")
        self.assertEqual(params["filler_words"][0], "true")
        self.assertEqual(params["utterances"][0], "true")
        self.assertEqual(params["keyterm"][0], "PeirsonPatterson")

    def test_mock_transcription_returns_request_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = _make_audio(Path(temp_dir) / "audio.wav")
            payload = transcribe_prerecorded(
                case_id=12,
                audio_path=audio_path,
                utt_split=0.9,
                data_root=Path(temp_dir) / "data",
                mock=True,
            )

        self.assertIn("_request_metadata", payload)
        self.assertEqual(payload["_request_metadata"]["model"], "nova-3")
        self.assertTrue(payload["results"]["utterances"])
