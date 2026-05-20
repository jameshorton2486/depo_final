from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def build_export_manifest(
    *,
    session_id: int,
    case_id: int,
    export_type: str,
    exported_files: list[Path],
    transcript_metadata: dict[str, object],
    export_settings: dict[str, object],
    review_status: dict[str, object],
    preprocessing_metadata: dict[str, object],
) -> dict[str, object]:
    return {
        "session_id": session_id,
        "case_id": case_id,
        "export_type": export_type,
        "generated_at": datetime.now(UTC).isoformat(),
        "exported_files": [str(path) for path in exported_files],
        "transcript_metadata": transcript_metadata,
        "export_settings": export_settings,
        "review_status": review_status,
        "preprocessing_metadata": preprocessing_metadata,
    }
