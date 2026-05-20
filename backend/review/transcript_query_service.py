from __future__ import annotations

from pathlib import Path

from backend.database.repositories.assets_repo import get_assets_for_session
from backend.database.repositories.transcript_repo import (
    get_timeline_for_session,
    get_word_object,
)
from backend.review.confidence_queue import ensure_review_queue
from backend.review.confidence_service import classify_confidence, summarize_confidence
from backend.review.playback_service import (
    build_playback_bundle,
    build_word_playback_metadata,
)
from backend.review.review_utils import build_search_text, normalize_speaker_role
from backend.review.speaker_corrections import get_latest_speaker_corrections


def get_review_timeline(
    session_id: int,
    database_path: Path | None = None,
) -> dict[str, object]:
    timeline_models = get_timeline_for_session(session_id, database_path)
    assets = get_assets_for_session(session_id, database_path)
    blocks = [block.model_dump(mode="json") for block in timeline_models]
    enriched_blocks: list[dict[str, object]] = []
    speaker_corrections = get_latest_speaker_corrections(session_id, database_path)

    for block in blocks:
        correction = speaker_corrections.get(int(block.get("speaker_segment_id") or 0))
        if correction:
            block["speaker_label"] = correction["corrected_speaker_label"]
            block["speaker_role_override"] = correction.get("corrected_role")
        enriched_words = []
        for word in block.get("words", []):
            word["confidence_class"] = classify_confidence(word.get("confidence"))
            word["review_candidate"] = word["confidence_class"] == "low"
            word["display_text"] = word.get("modified_text") or word.get("word_text")
            if correction:
                word["speaker_label"] = correction["corrected_speaker_label"]
            enriched_words.append(word)
        block["words"] = enriched_words
        block["speaker_role"] = (
            correction.get("corrected_role")
            if correction and correction.get("corrected_role")
            else normalize_speaker_role(block.get("speaker_label"))
        )
        block["confidence_class"] = classify_confidence(block.get("confidence"))
        block["search_text"] = build_search_text(block)
        block["review_candidate_count"] = sum(
            1 for word in enriched_words if word["review_candidate"]
        )
        enriched_blocks.append(block)

    primary_asset = assets[0].model_dump(mode="json") if assets else None
    playback = build_playback_bundle(
        enriched_blocks,
        media_path=primary_asset["file_path"] if primary_asset else None,
    )
    playback["media_url"] = f"/api/transcript/{session_id}/media" if primary_asset else None
    return {
        "session_id": session_id,
        "asset": primary_asset,
        "timeline": enriched_blocks,
        "confidence_summary": summarize_confidence(playback["word_timeline"]),
        "playback": playback,
        "review_queue": ensure_review_queue(session_id, database_path),
    }


def get_review_word(
    session_id: int,
    word_id: int,
    database_path: Path | None = None,
) -> dict[str, object]:
    word_payload = get_word_object(word_id, database_path)
    if int(word_payload["session_id"]) != session_id:
        raise LookupError(f"Word {word_id} was not found in session {session_id}.")
    speaker_correction = get_latest_speaker_corrections(session_id, database_path).get(
        int(word_payload.get("speaker_segment_id") or 0)
    )
    if speaker_correction:
        word_payload["speaker_label"] = speaker_correction["corrected_speaker_label"]
    return build_word_playback_metadata(word_payload)


def get_review_media_path(
    session_id: int,
    database_path: Path | None = None,
) -> Path:
    assets = get_assets_for_session(session_id, database_path)
    if not assets:
        raise LookupError(f"No transcript asset was found for session {session_id}.")
    media_path = Path(assets[0].file_path)
    if not media_path.exists():
        raise LookupError(f"Transcript media asset is missing for session {session_id}.")
    return media_path
