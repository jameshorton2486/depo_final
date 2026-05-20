from __future__ import annotations

import re

FEMALE_FIRST_NAMES = {
    "elizabeth",
    "lori",
    "karen",
    "tiffany",
    "delia",
    "flora",
    "susan",
    "maria",
    "anna",
}
MALE_FIRST_NAMES = {
    "wayne",
    "jacob",
    "curtis",
    "steven",
    "heath",
    "shawn",
    "yang",
    "coleman",
}


def generate_speaker_label(
    full_name: str, honorific: str | None = None, preserve: str | None = None
) -> str | None:
    if preserve:
        return preserve
    if not full_name.strip():
        return None
    parts = [part for part in re.split(r"\s+", full_name.strip()) if part]
    if not parts:
        return None
    last_name = re.sub(r"[^A-Za-z'-]", "", parts[-1]).upper()
    prefix = infer_prefix(parts[0], honorific)
    if prefix is None or not last_name:
        return None
    return f"{prefix}. {last_name}"


def infer_prefix(first_name: str, honorific: str | None = None) -> str | None:
    lowered_honorific = (honorific or "").strip(". ").lower()
    if lowered_honorific in {"mr", "mister"}:
        return "MR"
    if lowered_honorific in {"ms", "mrs", "miss"}:
        return "MS"
    lowered_name = first_name.lower()
    if lowered_name in FEMALE_FIRST_NAMES:
        return "MS"
    if lowered_name in MALE_FIRST_NAMES:
        return "MR"
    return None
