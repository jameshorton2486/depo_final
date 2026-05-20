from __future__ import annotations

import json
from pathlib import Path

from backend.database.connection import open_connection
from backend.database.models.transcript_models import (
    BlockType,
    SpeakerSegmentCreate,
    TranscriptAssetCreate,
    TranscriptBlockCreate,
    WordObjectCreate,
)
from backend.database.repositories.assets_repo import create_transcript_asset
from backend.database.repositories.transcript_repo import (
    create_speaker_segment,
    create_transcript_block,
    insert_word_object,
)


def create_live_stream_asset(
    *,
    session_id: int,
    case_id: int,
    source_label: str,
    data_root: Path,
    keyterms_path: str | None,
    phonetics_path: str | None,
    database_path: Path | None = None,
) -> dict[str, object]:
    raw_root = data_root / "cases" / str(case_id) / "raw" / f"live_session_{session_id}"
    raw_root.mkdir(parents=True, exist_ok=True)
    raw_json_path = raw_root / "realtime_stream.jsonl"
    metadata_path = raw_root / "realtime_metadata.json"
    asset = create_transcript_asset(
        TranscriptAssetCreate(
            session_id=session_id,
            asset_type="live_stream",
            file_name=f"{source_label}_session_{session_id}.pcm",
            file_path=str(raw_root / "live_stream.pcm"),
            source_format="pcm",
            deepgram_json_path=str(raw_json_path),
            keyterms_path=keyterms_path,
            preprocessing_metadata_path=str(metadata_path),
            is_primary=False,
        ),
        database_path,
    )
    metadata_path.write_text(
        json.dumps({"source_label": source_label, "phonetics_path": phonetics_path}, indent=2),
        encoding="utf-8",
    )
    return {
        "asset": asset,
        "raw_json_path": raw_json_path,
        "metadata_path": metadata_path,
    }


def append_raw_event(raw_json_path: Path, event: dict[str, object]) -> None:
    with raw_json_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")


def log_session_event(
    session_id: int,
    event_type: str,
    *,
    event_time: float | None,
    details: dict[str, object],
    database_path: Path | None = None,
) -> None:
    with open_connection(database_path) as connection:
        connection.execute(
            """
            INSERT INTO session_events (session_id, event_type, event_time, details_json)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, event_type, event_time, json.dumps(details)),
        )
        connection.commit()


def persist_live_utterance(
    *,
    session_id: int,
    transcript_asset_id: int,
    speaker_label: str,
    utterance: dict[str, object],
    database_path: Path | None = None,
) -> dict[str, object]:
    block_index = _next_block_index(session_id, database_path)
    speaker_segment = create_speaker_segment(
        SpeakerSegmentCreate(
            session_id=session_id,
            transcript_asset_id=transcript_asset_id,
            speaker_index=int(utterance["speaker"]),
            speaker_label=speaker_label,
            start_time=float(utterance["start"]),
            end_time=float(utterance["end"]),
            confidence=float(utterance.get("confidence") or 0.0),
        ),
        database_path,
    )
    block = create_transcript_block(
        TranscriptBlockCreate(
            session_id=session_id,
            speaker_segment_id=speaker_segment.id,
            block_index=block_index,
            block_type=_infer_block_type(speaker_label),
            speaker_index=int(utterance["speaker"]),
            raw_text=str(utterance["transcript"]),
            working_text=None,
            start_time=float(utterance["start"]),
            end_time=float(utterance["end"]),
            confidence=float(utterance.get("confidence") or 0.0),
            is_edited=False,
        ),
        database_path,
    )
    words: list[dict[str, object]] = []
    for word_index, word in enumerate(utterance.get("words", [])):
        word_record = insert_word_object(
            WordObjectCreate(
                transcript_block_id=block.id,
                word_index=word_index,
                word_text=str(word.get("punctuated_word") or word.get("word")),
                modified_text=None,
                start_time=float(word["start"]),
                end_time=float(word["end"]),
                confidence=float(word.get("confidence") or 0.0),
                is_filler=False,
            ),
            database_path,
        )
        words.append(word_record.model_dump(mode="json"))
    block_payload = block.model_dump(mode="json")
    block_payload["speaker_label"] = speaker_label
    block_payload["words"] = words
    return block_payload


def _next_block_index(session_id: int, database_path: Path | None = None) -> int:
    with open_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT COALESCE(MAX(block_index), -1) AS max_block_index
            FROM transcript_blocks
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
    return int(row["max_block_index"]) + 1


def _infer_block_type(speaker_label: str) -> BlockType:
    label = speaker_label.upper()
    if label.startswith("THE REPORTER"):
        return BlockType.REPORTER_STATEMENT
    if label.startswith("THE INTERPRETER"):
        return BlockType.INTERPRETER_STATEMENT
    if label.startswith("Q.") or label == "Q":
        return BlockType.EXAMINATION_Q
    if label.startswith("A.") or label == "A":
        return BlockType.EXAMINATION_A
    return BlockType.COLLOQUY
