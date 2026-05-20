from __future__ import annotations

from backend.database.models.transcript_models import TranscriptBlockCreate


def build_transcript_block(
    payload: dict[str, object],
    speaker_segment_id: int | None,
) -> TranscriptBlockCreate:
    block_payload = dict(payload)
    block_payload["speaker_segment_id"] = speaker_segment_id
    block_payload.pop("speaker_segment", None)
    block_payload.pop("words", None)
    return TranscriptBlockCreate(**block_payload)
