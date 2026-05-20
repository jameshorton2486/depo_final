from __future__ import annotations

import re

from backend.entities.parser_utils import non_empty_lines

FIRM_HINT_RE = re.compile(
    r"\b(LLP|LLC|PLLC|P\.C\.|PC|Law Firm|Law Offices|Legal Solutions|Attorneys|Partners)\b",
    re.IGNORECASE,
)


def extract_firm_names(text: str) -> list[str]:
    firms: list[str] = []
    for line in non_empty_lines(text):
        if FIRM_HINT_RE.search(line):
            firms.append(line.strip())
    return list(dict.fromkeys(firms))
