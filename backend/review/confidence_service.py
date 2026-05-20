from __future__ import annotations

CONFIDENCE_THRESHOLDS = {
    "high": 0.95,
    "medium": 0.85,
}


def classify_confidence(confidence: float | None) -> str:
    if confidence is None:
        return "medium"
    if confidence >= CONFIDENCE_THRESHOLDS["high"]:
        return "high"
    if confidence >= CONFIDENCE_THRESHOLDS["medium"]:
        return "medium"
    return "low"


def summarize_confidence(words: list[dict[str, object]]) -> dict[str, int]:
    summary = {"high": 0, "medium": 0, "low": 0}
    for word in words:
        summary[classify_confidence(word.get("confidence"))] += 1
    return summary
