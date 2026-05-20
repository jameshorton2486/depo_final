from __future__ import annotations

import re

from backend.database.models.transcript_models import ReviewIssueCategory


def normalize_repeated_spacing(text: str) -> str:
    return re.sub(r"\s{2,}", " ", text).strip()


def normalize_punctuation_spacing(text: str) -> str:
    text = re.sub(r"\s+([,.;:?!])", r"\1", text)
    return re.sub(r"([,.;:?!])([^\s])", r"\1 \2", text)


def normalize_speaker_label(label: str) -> str:
    normalized = normalize_repeated_spacing(label.upper().replace(" .", "."))
    normalized = re.sub(r"\bMR\s+", "MR. ", normalized)
    normalized = re.sub(r"\bMS\s+", "MS. ", normalized)
    normalized = re.sub(r"\bMRS\s+", "MRS. ", normalized)
    return normalized.strip()


def normalize_interruption_markers(text: str) -> str:
    text = text.replace(" - - ", " -- ").replace("-- ", "-- ").replace(" --", " --")
    text = re.sub(r"\s*--\s*", " -- ", text)
    return normalize_repeated_spacing(text)


def normalize_qa_spacing(text: str) -> str:
    text = re.sub(r"\bQ\.\s*", "Q. ", text)
    text = re.sub(r"\bA\.\s*", "A. ", text)
    return normalize_repeated_spacing(text)


def normalize_parenthetical_spacing(text: str) -> str:
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    return normalize_repeated_spacing(text)


def apply_deterministic_rules(
    value: str,
    issue_category: ReviewIssueCategory | str,
) -> dict[str, object]:
    category = (
        issue_category
        if isinstance(issue_category, ReviewIssueCategory)
        else ReviewIssueCategory(str(issue_category))
    )
    updated = value
    rules_applied: list[str] = []

    def _apply(rule_name: str, rule_func) -> None:
        nonlocal updated
        next_value = rule_func(updated)
        if next_value != updated:
            updated = next_value
            rules_applied.append(rule_name)

    _apply("normalize_repeated_spacing", normalize_repeated_spacing)
    if category in {
        ReviewIssueCategory.COLLOQUY_FORMAT,
        ReviewIssueCategory.OBJECTION_FORMAT,
        ReviewIssueCategory.LOW_CONFIDENCE,
    }:
        _apply("normalize_punctuation_spacing", normalize_punctuation_spacing)
        _apply("normalize_qa_spacing", normalize_qa_spacing)
        _apply("normalize_parenthetical_spacing", normalize_parenthetical_spacing)
    if category == ReviewIssueCategory.INTERRUPTED_SPEECH:
        _apply("normalize_interruption_markers", normalize_interruption_markers)
    if category == ReviewIssueCategory.POSSIBLE_SPEAKER_ERROR:
        _apply("normalize_speaker_label", normalize_speaker_label)

    return {
        "original_value": value,
        "updated_value": updated,
        "changed": updated != value,
        "rules_applied": rules_applied,
    }
