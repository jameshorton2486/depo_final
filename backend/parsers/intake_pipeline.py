from __future__ import annotations

from backend.parsers.entity_pipeline import process_intake_text
from backend.parsers.intake_parser import read_intake_source


def run_intake_pipeline(
    *,
    pasted_text: str | None = None,
    file_name: str | None = None,
    file_content_base64: str | None = None,
    intake_metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    source = read_intake_source(
        pasted_text=pasted_text,
        file_name=file_name,
        file_content_base64=file_content_base64,
    )
    metadata = dict(intake_metadata or {})
    metadata.setdefault("source_document", source.file_name or "Pasted Intake")
    return process_intake_text(source.text, source.extracted_from, metadata)
