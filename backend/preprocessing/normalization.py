from __future__ import annotations

HIGH_PASS_HZ = 85
TARGET_LUFS = -16
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1


def build_normalization_filter() -> str:
    return f"highpass=f={HIGH_PASS_HZ},loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11"
