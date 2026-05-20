from __future__ import annotations

from pathlib import Path

from backend.preprocessing.ffmpeg_pipeline import apply_light_denoise


def apply_conditional_rnnoise(source_path: Path, target_path: Path) -> dict[str, object]:
    apply_light_denoise(source_path, target_path)
    return {
        "denoise_applied": True,
        "denoise_method": "light_ffmpeg_fallback",
        "output_path": str(target_path),
    }
