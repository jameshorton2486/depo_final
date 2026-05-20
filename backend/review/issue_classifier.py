from __future__ import annotations

from backend.database.models.transcript_models import ReviewIssueCategory


def classify_word_issues(
    word: dict[str, object], block: dict[str, object]
) -> list[ReviewIssueCategory]:
    issues: list[ReviewIssueCategory] = []
    confidence = word.get("confidence")
    if isinstance(confidence, (int, float)) and float(confidence) < 0.85:
        issues.append(ReviewIssueCategory.LOW_CONFIDENCE)
    if bool(word.get("is_filler")):
        issues.append(ReviewIssueCategory.FILLER_WORD)

    label = str(block.get("speaker_label") or "").upper()
    if not label or label.startswith("SPEAKER "):
        issues.append(ReviewIssueCategory.POSSIBLE_SPEAKER_ERROR)

    token = str(word.get("word_text") or "")
    if "--" in token:
        issues.append(ReviewIssueCategory.INTERRUPTED_SPEECH)
    if "'" in token and len(token) > 2:
        issues.append(ReviewIssueCategory.PHONETIC_UNCERTAINTY)
    return issues


def classify_block_issues(block: dict[str, object]) -> list[ReviewIssueCategory]:
    issues: list[ReviewIssueCategory] = []
    raw_text = str(block.get("raw_text") or "")
    block_type = str(block.get("block_type") or "")

    if "  " in raw_text or " ," in raw_text or " ." in raw_text:
        if block_type == "OBJECTION":
            issues.append(ReviewIssueCategory.OBJECTION_FORMAT)
        else:
            issues.append(ReviewIssueCategory.COLLOQUY_FORMAT)
    if block_type == "OBJECTION":
        normalized = raw_text.upper()
        if not normalized.startswith("OBJECTION"):
            issues.append(ReviewIssueCategory.OBJECTION_FORMAT)
    return issues
