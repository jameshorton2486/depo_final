from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import soundfile as sf


def estimate_snr_db(audio_path: Path) -> float:
    audio, sample_rate = sf.read(str(audio_path), always_2d=False)
    if isinstance(audio, tuple):
        audio = audio[0]
    samples = np.asarray(audio, dtype=np.float32)
    if samples.ndim > 1:
        samples = np.mean(samples, axis=1)
    if not samples.size:
        return 0.0

    frame_size = max(1, int(sample_rate * 0.05))
    frame_rms = []
    for start in range(0, len(samples), frame_size):
        frame = samples[start : start + frame_size]
        if frame.size:
            frame_rms.append(float(np.sqrt(np.mean(np.square(frame)) + 1e-12)))

    if not frame_rms:
        return 0.0

    signal_level = max(np.percentile(frame_rms, 85), 1e-6)
    noise_level = max(np.percentile(frame_rms, 20), 1e-6)
    snr = 20 * math.log10(signal_level / noise_level)
    return round(float(max(-5.0, min(45.0, snr))), 2)
