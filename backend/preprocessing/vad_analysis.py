from __future__ import annotations

import statistics
from functools import lru_cache
from pathlib import Path

import soundfile as sf
import torch
import torchaudio.functional as audio_functional
from silero_vad import get_speech_timestamps, load_silero_vad

from backend.preprocessing.normalization import TARGET_SAMPLE_RATE


@lru_cache(maxsize=1)
def _model():
    return load_silero_vad()


def analyze_vad(audio_path: Path, max_seconds: int = 90) -> dict[str, object]:
    samples, sample_rate = sf.read(str(audio_path), always_2d=False)
    waveform = torch.tensor(samples, dtype=torch.float32)
    if waveform.ndim > 1:
        waveform = waveform.mean(dim=1)
    limit = min(int(sample_rate * max_seconds), int(waveform.numel()))
    waveform = waveform[:limit]
    if sample_rate != TARGET_SAMPLE_RATE:
        waveform = audio_functional.resample(waveform, sample_rate, TARGET_SAMPLE_RATE)
        sample_rate = TARGET_SAMPLE_RATE

    speech_timestamps = get_speech_timestamps(waveform, _model(), sampling_rate=sample_rate)
    segments = [
        {
            "start": round(item["start"] / sample_rate, 3),
            "end": round(item["end"] / sample_rate, 3),
        }
        for item in speech_timestamps
    ]
    if not segments and float(torch.sqrt(torch.mean(waveform**2) + 1e-12)) > 0.01:
        segments = [{"start": 0.0, "end": round(waveform.numel() / sample_rate, 3)}]
    gaps = [
        round(segments[index]["start"] - segments[index - 1]["end"], 3)
        for index in range(1, len(segments))
        if segments[index]["start"] > segments[index - 1]["end"]
    ]
    median_gap = statistics.median(gaps) if gaps else 0.8
    utt_split = max(0.5, min(1.5, float(median_gap)))
    return {
        "analyzed_seconds": round(waveform.numel() / sample_rate, 2),
        "speech_segments": segments,
        "speech_segment_count": len(segments),
        "median_gap": round(float(median_gap), 3),
        "calibrated_utt_split": round(utt_split, 3),
    }
