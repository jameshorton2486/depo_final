from __future__ import annotations

import re

from backend.database.models.transcript_models import TranscriptTimelineBlock

EXHIBIT_PATTERN = re.compile(
    r"\b(?P<label>(?:Plaintiff|Defendant)\s+Exhibit\s+[A-Z]|\bExhibit\s+\d+)\b",
    re.IGNORECASE,
)


def build_exhibit_index(blocks: list[TranscriptTimelineBlock]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    seen: set[str] = set()
    for block in blocks:
        text = block.working_text or block.raw_text
        if not text:
            continue
        for match in EXHIBIT_PATTERN.finditer(text):
            label = " ".join(match.group("label").split())
            key = label.lower()
            if key in seen:
                continue
            seen.add(key)
            entries.append(
                {
                    "label": label,
                    "description": text.strip(),
                    "block_index": block.block_index,
                    "start_time": block.start_time,
                }
            )
    return entries
