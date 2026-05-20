from __future__ import annotations

from backend.review.confidence_service import classify_confidence
from backend.review.review_utils import normalize_speaker_role


def build_playback_bundle(
    timeline: list[dict[str, object]],
    *,
    media_path: str | None,
) -> dict[str, object]:
    flattened_words: list[dict[str, object]] = []
    for block_index, block in enumerate(timeline):
        words = block.get("words", [])
        for word_index, word in enumerate(words):
            flattened_words.append(
                {
                    "word_id": word["id"],
                    "block_id": block["id"],
                    "block_index": block_index,
                    "word_index": word_index,
                    "speaker_label": block.get("speaker_label"),
                    "speaker_role": normalize_speaker_role(block.get("speaker_label")),
                    "start_time": word["start_time"],
                    "end_time": word["end_time"],
                    "confidence": word.get("confidence"),
                    "confidence_class": classify_confidence(word.get("confidence")),
                }
            )

    duration = 0.0
    if timeline:
        duration = float(timeline[-1].get("end_time") or 0.0)
    return {
        "media_path": media_path,
        "duration": duration,
        "word_timeline": flattened_words,
    }


def build_word_playback_metadata(word_payload: dict[str, object]) -> dict[str, object]:
    return {
        **word_payload,
        "confidence_class": classify_confidence(word_payload.get("confidence")),
        "speaker_role": normalize_speaker_role(word_payload.get("speaker_label")),
        "seek_time": word_payload.get("start_time"),
    }
