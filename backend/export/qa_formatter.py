from __future__ import annotations

from backend.database.models.transcript_models import BlockType, TranscriptTimelineBlock

QA_LEFT_TWIPS = 720
QA_HANGING_TWIPS = 360


def format_qa_block(block: TranscriptTimelineBlock) -> dict[str, object]:
    if block.block_type not in {BlockType.EXAMINATION_Q, BlockType.EXAMINATION_A}:
        raise ValueError("Q/A formatter only supports examination blocks.")
    prefix = "Q." if block.block_type == BlockType.EXAMINATION_Q else "A."
    text = (block.working_text or block.raw_text or "").strip()
    return {
        "style": "qa",
        "prefix": prefix,
        "label": prefix,
        "text": text,
        "runs": [prefix, "\t", text],
        "left_twips": QA_LEFT_TWIPS,
        "hanging_twips": QA_HANGING_TWIPS,
    }
