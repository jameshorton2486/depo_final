from __future__ import annotations

import subprocess
from pathlib import Path

from backend.preprocessing.normalization import (
    TARGET_CHANNELS,
    TARGET_SAMPLE_RATE,
    build_normalization_filter,
)


def transcode_to_pcm(source_path: Path, target_path: Path) -> Path:
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-ac",
            str(TARGET_CHANNELS),
            "-ar",
            str(TARGET_SAMPLE_RATE),
            "-c:a",
            "pcm_s16le",
            str(target_path),
        ]
    )
    return target_path


def normalize_audio(source_path: Path, target_path: Path) -> Path:
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-af",
            build_normalization_filter(),
            "-ac",
            str(TARGET_CHANNELS),
            "-ar",
            str(TARGET_SAMPLE_RATE),
            "-c:a",
            "pcm_s16le",
            str(target_path),
        ]
    )
    return target_path


def apply_light_denoise(source_path: Path, target_path: Path) -> Path:
    _run_ffmpeg(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-af",
            "afftdn=nf=-25",
            "-ac",
            str(TARGET_CHANNELS),
            "-ar",
            str(TARGET_SAMPLE_RATE),
            "-c:a",
            "pcm_s16le",
            str(target_path),
        ]
    )
    return target_path


def _run_ffmpeg(command: list[str]) -> None:
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or "ffmpeg preprocessing failed.")
