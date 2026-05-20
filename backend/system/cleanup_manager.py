from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from backend.config import settings


def collect_cleanup_targets(data_root: Path | None = None) -> dict[str, object]:
    resolved_root = data_root if data_root is not None else settings.data_root
    temp_root = resolved_root / "temp"
    temp_root.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(UTC) - timedelta(days=1)
    stale_files: list[str] = []
    for path in temp_root.rglob("*"):
        if not path.is_file():
            continue
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        if modified < cutoff:
            stale_files.append(str(path))
    return {
        "temp_root": str(temp_root),
        "stale_temp_files": stale_files,
        "stale_temp_count": len(stale_files),
    }
