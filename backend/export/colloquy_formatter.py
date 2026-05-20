from __future__ import annotations

from backend.database.models.transcript_models import BlockType, TranscriptTimelineBlock

COLLOQUY_LEFT_TWIPS = 360
COLLOQUY_HANGING_TWIPS = 360


def format_colloquy_block(block: TranscriptTimelineBlock) -> dict[str, object]:
    speaker_label = (block.speaker_label or _fallback_label(block)).strip()
    text = (block.working_text or block.raw_text or "").strip()
    label = f"{speaker_label}:"
    return {
        "style": "colloquy",
        "prefix": label,
        "label": speaker_label,
        "text": text,
        "runs": [label, "\t", text],
        "left_twips": COLLOQUY_LEFT_TWIPS,
        "hanging_twips": COLLOQUY_HANGING_TWIPS,
    }


def _fallback_label(block: TranscriptTimelineBlock) -> str:
    if block.block_type == BlockType.REPORTER_STATEMENT:
        return "THE REPORTER"
    if block.block_type == BlockType.INTERPRETER_STATEMENT:
        return "THE INTERPRETER"
    if block.block_type == BlockType.OBJECTION:
        return "OBJECTION"
    if block.block_type == BlockType.PROCEEDINGS:
        return "PROCEEDINGS"
    return "SPEAKER"
