from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from backend.config import settings


def ensure_log_root(data_root: Path | None = None) -> Path:
    root = data_root if data_root is not None else settings.data_root
    log_root = root / "logs"
    log_root.mkdir(parents=True, exist_ok=True)
    return log_root


def write_log_event(
    channel: str,
    message: str,
    *,
    payload: dict[str, object] | None = None,
    data_root: Path | None = None,
) -> Path:
    log_root = ensure_log_root(data_root)
    timestamp = datetime.now(UTC).isoformat()
    log_path = log_root / f"{channel}.log"
    fragments = [timestamp, message]
    if payload:
        rendered = ", ".join(f"{key}={value}" for key, value in sorted(payload.items()))
        fragments.append(rendered)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(" | ".join(fragments) + "\n")
    return log_path
