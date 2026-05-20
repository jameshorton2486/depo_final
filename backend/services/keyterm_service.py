from __future__ import annotations

import json
from pathlib import Path

from backend.config import settings


def write_keyterms(case_id: int, payload: dict[str, object]) -> Path:
    case_dir = settings.data_root / "cases" / str(case_id)
    case_dir.mkdir(parents=True, exist_ok=True)
    output_path = case_dir / "keyterms.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
