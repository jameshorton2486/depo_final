from __future__ import annotations

from backend.database.connection import open_connection
from backend.database.models.transcript_models import BlockType


def map_transcript_payload(
    case_id: int,
    session_id: int,
    transcript_asset_id: int,
    parsed_response: dict[str, object],
    database_path=None,
) -> dict[str, object]:
    speaker_labels = _load_case_speaker_labels(case_id, database_path)
    speaker_segments: list[dict[str, object]] = []
    transcript_blocks: list[dict[str, object]] = []

    for utterance in parsed_response.get("utterances", []):
        speaker_index = int(utterance.get("speaker_index") or 0)
        segment = {
            "session_id": session_id,
            "transcript_asset_id": transcript_asset_id,
            "speaker_index": speaker_index,
            "speaker_label": speaker_labels.get(speaker_index) or f"SPEAKER {speaker_index + 1}",
            "start_time": float(utterance.get("start_time", 0.0)),
            "end_time": float(utterance.get("end_time", 0.0)),
            "confidence": utterance.get("confidence"),
        }
        speaker_segments.append(segment)
        transcript_blocks.append(
            {
                "session_id": session_id,
                "block_index": len(transcript_blocks) + 1,
                "block_type": _classify_block_type(
                    segment["speaker_label"],
                    str(utterance.get("transcript", "")),
                ),
                "speaker_index": speaker_index,
                "raw_text": str(utterance.get("transcript", "")),
                "start_time": segment["start_time"],
                "end_time": segment["end_time"],
                "confidence": utterance.get("confidence"),
                "speaker_segment": segment,
                "words": utterance.get("words", []),
            }
        )

    return {
        "speaker_segments": speaker_segments,
        "transcript_blocks": transcript_blocks,
    }


def _load_case_speaker_labels(case_id: int, database_path=None) -> dict[int, str]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT speaker_label
            FROM case_attorneys
            WHERE case_id = ? AND speaker_label IS NOT NULL AND speaker_label != ''
            ORDER BY id ASC
            """,
            (case_id,),
        ).fetchall()
    labels: dict[int, str] = {}
    for index, row in enumerate(rows):
        labels[index] = str(row["speaker_label"])
    return labels


def _classify_block_type(speaker_label: str, transcript: str) -> BlockType:
    normalized_label = speaker_label.upper()
    stripped = transcript.strip()
    normalized_text = stripped.upper()
    if normalized_label == "THE REPORTER":
        return BlockType.REPORTER_STATEMENT
    if normalized_label == "THE INTERPRETER":
        return BlockType.INTERPRETER_STATEMENT
    if normalized_text.startswith("(") and normalized_text.endswith(")"):
        return BlockType.PARENTHETICAL
    if "OBJECTION" in normalized_text:
        return BlockType.OBJECTION
    if stripped.endswith("?"):
        return BlockType.EXAMINATION_Q
    if normalized_text.startswith("OFF THE RECORD") or normalized_text.startswith(
        "BACK ON THE RECORD"
    ):
        return BlockType.PROCEEDINGS
    return BlockType.COLLOQUY
