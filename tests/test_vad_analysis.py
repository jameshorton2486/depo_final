from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from backend.preprocessing.vad_analysis import analyze_vad


def _make_vad_wav(path: Path) -> Path:
    sample_rate = 16000
    speech_a = 0.35 * np.sin(2 * math.pi * 180 * np.arange(sample_rate * 2) / sample_rate)
    gap = np.zeros(int(sample_rate * 0.8), dtype=np.float32)
    speech_b = 0.32 * np.sin(2 * math.pi * 200 * np.arange(sample_rate * 2) / sample_rate)
    samples = np.concatenate([speech_a, gap, speech_b]).astype(np.float32)
    sf.write(str(path), samples, sample_rate)
    return path


class VadAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.audio_path = _make_vad_wav(Path(self.temp_dir.name) / "vad.wav")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_vad_analysis_returns_calibrated_utt_split(self) -> None:
        payload = analyze_vad(self.audio_path)

        self.assertGreaterEqual(payload["speech_segment_count"], 1)
        self.assertGreaterEqual(float(payload["calibrated_utt_split"]), 0.5)
        self.assertLessEqual(float(payload["calibrated_utt_split"]), 1.5)
