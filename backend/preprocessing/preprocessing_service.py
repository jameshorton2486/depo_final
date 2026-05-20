from __future__ import annotations

import base64
import json
from pathlib import Path

from backend.config import settings
from backend.preprocessing.ffmpeg_pipeline import normalize_audio, transcode_to_pcm
from backend.preprocessing.rnnoise import apply_conditional_rnnoise
from backend.preprocessing.snr_estimation import estimate_snr_db
from backend.preprocessing.vad_analysis import analyze_vad


def preprocess_media(
    *,
    case_id: int,
    file_name: str,
    file_content_base64: str,
    data_root: Path | None = None,
) -> dict[str, object]:
    resolved_data_root = data_root if data_root is not None else settings.data_root
    case_dir = resolved_data_root / "cases" / str(case_id)
    uploads_dir = case_dir / "uploads"
    processed_dir = case_dir / "processed"
    raw_dir = case_dir / "raw"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    source_bytes = base64.b64decode(file_content_base64)
    original_path = uploads_dir / file_name
    original_path.write_bytes(source_bytes)

    stem = original_path.stem
    transcoded_path = processed_dir / f"{stem}_16k.wav"
    normalized_path = processed_dir / f"{stem}_normalized.wav"
    denoised_path = processed_dir / f"{stem}_denoised.wav"

    transcode_to_pcm(original_path, transcoded_path)
    normalize_audio(transcoded_path, normalized_path)
    snr_db = estimate_snr_db(normalized_path)

    final_audio_path = normalized_path
    denoise_metadata = {"denoise_applied": False, "denoise_method": None}
    if snr_db < 20:
        denoise_metadata = apply_conditional_rnnoise(normalized_path, denoised_path)
        final_audio_path = Path(str(denoise_metadata["output_path"]))

    vad_metadata = analyze_vad(final_audio_path)
    metadata = {
        "source_file_name": file_name,
        "original_path": str(original_path),
        "transcoded_path": str(transcoded_path),
        "normalized_path": str(normalized_path),
        "final_audio_path": str(final_audio_path),
        "estimated_snr_db": snr_db,
        "calibrated_utt_split": vad_metadata["calibrated_utt_split"],
        "denoise": denoise_metadata,
        "vad": vad_metadata,
    }
    metadata_path = raw_dir / f"{stem}_preprocessing.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    metadata["metadata_path"] = str(metadata_path)
    return metadata
