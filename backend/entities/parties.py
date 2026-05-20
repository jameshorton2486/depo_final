from __future__ import annotations

import re

from backend.entities.parser_utils import non_empty_lines, title_case_name

CAUSE_RE = re.compile(r"(?:CAUSE NO\.?|CIVIL ACTION NO\.?)\s*[:#]?\s*([A-Z0-9\-]+)", re.IGNORECASE)
VS_RE = re.compile(r"\bV(?:S\.?)?\b", re.IGNORECASE)


def extract_case_and_parties(text: str) -> dict[str, object]:
    lines = non_empty_lines(text)
    cause_number = None
    for line in lines:
        cause_match = CAUSE_RE.search(line)
        if cause_match:
            cause_number = cause_match.group(1)
            break

    case_style = _extract_case_style(lines)
    parties = _extract_parties(case_style)
    return {
        "case_style": case_style,
        "cause_number": cause_number,
        "parties": parties,
    }


def _extract_case_style(lines: list[str]) -> str | None:
    for index, line in enumerate(lines):
        if VS_RE.search(line):
            previous_line = lines[index - 1] if index > 0 else ""
            next_line = lines[index + 1] if index + 1 < len(lines) else ""
            left = previous_line if previous_line else line.split(" v. ")[0]
            right = next_line if next_line else line.split(" v. ")[-1]
            if left and right and left != right:
                return f"{title_case_name(left)} v. {title_case_name(right)}"
    joined = " ".join(lines[:6])
    match = re.search(
        r"([A-Z][A-Za-z0-9 .,&'-]+)\s+v\.?\s+([A-Z][A-Za-z0-9 .,&'-]+)", joined, re.IGNORECASE
    )
    if match:
        return f"{title_case_name(match.group(1))} v. {title_case_name(match.group(2))}"
    return None


def _extract_parties(case_style: str | None) -> list[dict[str, object]]:
    if not case_style or " v. " not in case_style:
        return []
    plaintiff, defendant = case_style.split(" v. ", 1)
    return [
        {
            "party_name": plaintiff.strip(),
            "party_type": "plaintiff",
            "side": "plaintiff",
            "role_modifier": None,
            "alias_name": _extract_alias(plaintiff),
            "entity_type": infer_entity_type(plaintiff),
            "related_party_name": None,
        },
        {
            "party_name": defendant.strip(),
            "party_type": "defendant",
            "side": "defendant",
            "role_modifier": None,
            "alias_name": _extract_alias(defendant),
            "entity_type": infer_entity_type(defendant),
            "related_party_name": None,
        },
    ]


def infer_entity_type(name: str) -> str:
    upper = name.upper()
    if any(token in upper for token in [" LLC", " L.L.C"]):
        return "llc"
    if any(token in upper for token in [" INC", " CORP", " CORPORATION", " COMPANY"]):
        return "corporation"
    if upper.startswith("STATE OF") or upper.startswith("UNITED STATES"):
        return "gov"
    return "individual"


def _extract_alias(name: str) -> str | None:
    match = re.search(r"(?:A/K/A|F/K/A|D/B/A)\s+(.+)$", name, re.IGNORECASE)
    return match.group(1).strip() if match else None
