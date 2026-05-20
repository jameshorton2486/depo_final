from __future__ import annotations


def search_live_blocks(blocks: list[dict[str, object]], query: str) -> list[dict[str, object]]:
    normalized = query.strip().lower()
    if not normalized:
        return blocks
    return [
        block
        for block in blocks
        if normalized in str(block.get("raw_text", "")).lower()
        or normalized in str(block.get("speaker_label", "")).lower()
    ]
