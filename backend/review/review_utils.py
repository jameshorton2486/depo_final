from __future__ import annotations


def normalize_speaker_role(label: str | None) -> str:
    if not label:
        return "unknown"
    normalized = label.upper()
    if normalized == "THE REPORTER":
        return "reporter"
    if normalized == "THE INTERPRETER":
        return "interpreter"
    if (
        normalized.startswith("MR.")
        or normalized.startswith("MS.")
        or normalized.startswith("MRS.")
    ):
        return "attorney"
    return "witness"


def build_search_text(block: dict[str, object]) -> str:
    parts = [
        str(block.get("speaker_label") or ""),
        str(block.get("raw_text") or ""),
        " ".join(str(word.get("word_text") or "") for word in block.get("words", [])),
    ]
    return " ".join(parts).strip().lower()
