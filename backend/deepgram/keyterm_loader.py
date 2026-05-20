from __future__ import annotations

import json
from pathlib import Path

from backend.config import settings


def load_case_prompting(case_id: int, data_root: Path | None = None) -> dict[str, object]:
    resolved_root = data_root if data_root is not None else settings.data_root
    case_dir = resolved_root / "cases" / str(case_id)
    keyterms_path = case_dir / "keyterms.json"
    phonetics_path = case_dir / "phonetics.json"
    keyterms_payload = _read_json(keyterms_path)
    phonetics_payload = _read_json(phonetics_path)

    prompted_terms: list[str] = []
    for item in keyterms_payload.get("keyterms", []):
        term = str(item.get("term", "")).strip()
        if term:
            prompted_terms.append(term)
    for item in phonetics_payload.get("generated", []):
        term = str(item.get("term", "")).strip()
        hint = str(item.get("pronunciation_hint", "")).strip()
        if term:
            prompted_terms.append(term)
        if hint:
            prompted_terms.append(hint)
    for item in phonetics_payload.get("manual_overrides", []):
        term = str(item.get("term", "")).strip()
        pronunciation = str(item.get("pronunciation", "")).strip()
        if term:
            prompted_terms.append(term)
        if pronunciation:
            prompted_terms.append(pronunciation)

    unique_terms: list[str] = []
    seen: set[str] = set()
    for term in prompted_terms:
        normalized = term.lower()
        if normalized in seen or not term:
            continue
        seen.add(normalized)
        unique_terms.append(term)

    return {
        "keyterms_path": str(keyterms_path) if keyterms_path.exists() else None,
        "phonetics_path": str(phonetics_path) if phonetics_path.exists() else None,
        "keyterms_payload": keyterms_payload,
        "phonetics_payload": phonetics_payload,
        "prompted_terms": unique_terms[:100],
    }


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
