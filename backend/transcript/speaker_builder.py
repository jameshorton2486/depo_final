from __future__ import annotations

from backend.database.models.transcript_models import SpeakerSegmentCreate


def build_speaker_segment(payload: dict[str, object]) -> SpeakerSegmentCreate:
    return SpeakerSegmentCreate(**payload)
