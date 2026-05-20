from __future__ import annotations

from backend.database.models.case_models import CaseRecord
from backend.database.models.session_models import SessionRecord
from backend.database.models.transcript_models import BlockType, TranscriptTimelineBlock
from backend.export.certificate_generator import build_certificate_page
from backend.export.colloquy_formatter import format_colloquy_block
from backend.export.exhibit_indexer import build_exhibit_index
from backend.export.pagination_engine import paginate_lines
from backend.export.qa_formatter import format_qa_block


def render_transcript_document(
    case_record: CaseRecord,
    session_record: SessionRecord,
    blocks: list[TranscriptTimelineBlock],
) -> dict[str, object]:
    paragraphs: list[dict[str, object]] = []
    lines: list[str] = []
    for block in blocks:
        paragraph = render_block(block)
        paragraphs.append(paragraph)
        lines.extend(paragraph_to_lines(paragraph))

    certificate_lines = build_certificate_page(case_record, session_record)
    exhibit_index = build_exhibit_index(blocks)
    pages = paginate_lines(lines)
    return {
        "case": case_record.model_dump(mode="json"),
        "session": session_record.model_dump(mode="json"),
        "paragraphs": paragraphs,
        "lines": lines,
        "pages": pages,
        "certificate_lines": certificate_lines,
        "exhibit_index": exhibit_index,
    }


def render_block(block: TranscriptTimelineBlock) -> dict[str, object]:
    if block.block_type in {BlockType.EXAMINATION_Q, BlockType.EXAMINATION_A}:
        return format_qa_block(block)
    if block.block_type == BlockType.PARENTHETICAL:
        text = (block.working_text or block.raw_text or "").strip()
        return {
            "style": "parenthetical",
            "prefix": "",
            "label": "",
            "text": f"({text.strip('()')})" if text else "",
            "runs": [f"({text.strip('()')})" if text else ""],
            "left_twips": 360,
            "hanging_twips": 0,
        }
    return format_colloquy_block(block)


def paragraph_to_lines(paragraph: dict[str, object]) -> list[str]:
    if paragraph["style"] == "qa":
        return [f"{paragraph['prefix']}\t{paragraph['text']}"]
    if paragraph["style"] == "parenthetical":
        return [str(paragraph["text"])]
    return [f"{paragraph['prefix']}\t{paragraph['text']}"]
