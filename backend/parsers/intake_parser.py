from __future__ import annotations

import base64
import io
from dataclasses import dataclass

from pypdf import PdfReader

from backend.entities.parser_utils import normalize_whitespace


@dataclass
class IntakeSource:
    file_name: str | None
    extracted_from: str
    text: str


def read_intake_source(
    *,
    pasted_text: str | None = None,
    file_name: str | None = None,
    file_content_base64: str | None = None,
) -> IntakeSource:
    if file_content_base64 and file_name:
        raw_bytes = base64.b64decode(file_content_base64)
        if file_name.lower().endswith(".pdf"):
            text = _extract_pdf_text(raw_bytes)
            extracted_from = "NOD"
        else:
            text = raw_bytes.decode("utf-8", errors="ignore")
            extracted_from = "Intake Sheet"
        return IntakeSource(
            file_name=file_name, extracted_from=extracted_from, text=normalize_whitespace(text)
        )
    if pasted_text:
        return IntakeSource(
            file_name=None, extracted_from="Manual", text=normalize_whitespace(pasted_text)
        )
    raise ValueError("Either pasted_text or file_content_base64 is required.")


def _extract_pdf_text(raw_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(raw_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
