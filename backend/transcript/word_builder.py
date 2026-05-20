from __future__ import annotations

from backend.database.models.transcript_models import WordObjectCreate


def build_word_object(
    transcript_block_id: int,
    payload: dict[str, object],
) -> WordObjectCreate:
    word_payload = dict(payload)
    word_payload["transcript_block_id"] = transcript_block_id
    return WordObjectCreate(**word_payload)
