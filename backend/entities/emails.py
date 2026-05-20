from __future__ import annotations

import re

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def extract_emails(text: str) -> list[str]:
    return sorted({match.group(0).lower() for match in EMAIL_RE.finditer(text)})
