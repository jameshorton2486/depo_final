from __future__ import annotations

import re
from datetime import datetime


def normalize_whitespace(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\r", "\n")).strip()


def non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def title_case_name(value: str) -> str:
    tokens = [token for token in re.split(r"\s+", value.strip()) if token]
    return " ".join(
        token if token.isupper() and len(token) <= 3 else token.title() for token in tokens
    )


def parse_date_string(value: str) -> str | None:
    cleaned = value.strip().replace(",", "")
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(cleaned, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def slugify_filename(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return slug or "intake_source"
