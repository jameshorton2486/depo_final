from __future__ import annotations

import json
from pathlib import Path

from backend.config import settings


def store_raw_payloads(
    *,
    case_id: int,
    stem: str,
    raw_response: dict[str, object],
    request_metadata: dict[str, object],
    preprocessing_metadata: dict[str, object],
    data_root: Path | None = None,
) -> dict[str, Path]:
    resolved_root = data_root if data_root is not None else settings.data_root
    raw_dir = resolved_root / "cases" / str(case_id) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_json_path = raw_dir / f"{stem}_deepgram.json"
    request_metadata_path = raw_dir / f"{stem}_request.json"
    preprocessing_metadata_path = raw_dir / f"{stem}_preprocessing.json"

    raw_json_path.write_text(json.dumps(raw_response, indent=2), encoding="utf-8")
    request_metadata_path.write_text(json.dumps(request_metadata, indent=2), encoding="utf-8")
    preprocessing_metadata_path.write_text(
        json.dumps(preprocessing_metadata, indent=2), encoding="utf-8"
    )
    return {
        "raw_json_path": raw_json_path,
        "request_metadata_path": request_metadata_path,
        "preprocessing_metadata_path": preprocessing_metadata_path,
    }
