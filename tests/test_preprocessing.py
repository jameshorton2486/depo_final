from __future__ import annotations

import base64
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from backend.preprocessing.preprocessing_service import preprocess_media


def _make_sample_wav(path: Path, seconds: float = 8.0) -> Path:
    sample_rate = 16000
    total_frames = int(sample_rate * seconds)
    timeline = np.arange(total_frames) / sample_rate
    tone = 0.28 * np.sin(2 * math.pi * 220 * timeline)
    silence = np.zeros(sample_rate, dtype=np.float32)
    noise = 0.012 * np.random.default_rng(42).normal(size=total_frames).astype(np.float32)
    samples = tone.astype(np.float32) + noise
    samples[: silence.size] = silence
    sf.write(str(path), samples, sample_rate)
    return path


class PreprocessingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.audio_path = _make_sample_wav(self.root / "sample.wav")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_preprocessing_creates_processed_audio_and_metadata(self) -> None:
        payload = preprocess_media(
            case_id=77,
            file_name=self.audio_path.name,
            file_content_base64=base64.b64encode(self.audio_path.read_bytes()).decode("utf-8"),
            data_root=self.root / "data",
        )

        self.assertTrue(Path(str(payload["final_audio_path"])).exists())
        self.assertTrue(Path(str(payload["metadata_path"])).exists())
        self.assertGreaterEqual(float(payload["estimated_snr_db"]), -5.0)
        self.assertGreaterEqual(float(payload["calibrated_utt_split"]), 0.5)
        self.assertLessEqual(float(payload["calibrated_utt_split"]), 1.5)
