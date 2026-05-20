from __future__ import annotations

import re

from backend.entities.addresses import extract_addresses
from backend.entities.emails import extract_emails
from backend.entities.firms import extract_firm_names
from backend.entities.parser_utils import non_empty_lines, title_case_name

PHONE_RE = re.compile(r"(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})")
BAR_RE = re.compile(r"State Bar No\.?\s*(\d+)", re.IGNORECASE)
NAME_RE = re.compile(r"^(Mr\.|Ms\.|Mrs\.)?\s*([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,4})$")
REPRESENTS_RE = re.compile(r"ATTORNEYS?\s+FOR\s+(.+)$", re.IGNORECASE)


def extract_attorneys(text: str) -> list[dict[str, object | None]]:
    lines = non_empty_lines(text)
    attorneys: list[dict[str, object | None]] = []
    emails = extract_emails(text)
    for email in emails:
        email_index = next(
            (index for index, line in enumerate(lines) if email in line.lower()), None
        )
        if email_index is None:
            continue
        window = lines[max(0, email_index - 6) : min(len(lines), email_index + 4)]
        name_line, honorific = _find_name_line(window)
        if not name_line:
            continue
        full_name = title_case_name(name_line)
        firm_name = next(
            (firm for firm in extract_firm_names("\n".join(window)) if firm != name_line), None
        )
        address = extract_addresses("\n".join(window))
        represents = _find_represents_party(lines, email_index)
        attorneys.append(
            {
                "full_name": full_name,
                "law_firm": firm_name,
                "email": email,
                "phone": _first_match(PHONE_RE, "\n".join(window)),
                "fax": _find_fax(window),
                "bar_number": _first_match(BAR_RE, "\n".join(window)),
                "bar_state": "TX" if "state bar no" in "\n".join(window).lower() else None,
                "represented_party": represents,
                "honorific": honorific,
                "address_line_1": address[0]["address_line_1"] if address else None,
                "city": address[0]["city"] if address else None,
                "state": address[0]["state"] if address else None,
                "postal_code": address[0]["postal_code"] if address else None,
                "role": "appearing_attorney",
                "is_lead": bool("ordering attorney" in "\n".join(window).lower() or represents),
            }
        )
    deduped = []
    seen = set()
    for attorney in attorneys:
        key = (attorney["full_name"], attorney["email"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(attorney)
    return deduped


def _find_name_line(window: list[str]) -> tuple[str | None, str | None]:
    for line in window:
        clean = re.sub(r",\s*Esq\.?", "", line, flags=re.IGNORECASE).strip()
        match = NAME_RE.match(clean)
        if match:
            return match.group(2), match.group(1)
    return None, None


def _find_represents_party(lines: list[str], email_index: int) -> str | None:
    search_lines = lines[max(0, email_index - 4) : min(len(lines), email_index + 4)]
    for line in search_lines:
        match = REPRESENTS_RE.search(line)
        if match:
            represented = match.group(1).strip(" .")
            if represented.upper() in {"PLAINTIFF", "DEFENDANT", "INTERVENOR"}:
                return represented.title()
            return title_case_name(represented) if represented else None
    return None


def _first_match(pattern, text: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1) if match.groups() else match.group(0)


def _find_fax(window: list[str]) -> str | None:
    for line in window:
        if "fax" in line.lower():
            phone = PHONE_RE.search(line)
            if phone:
                return phone.group(0)
    return None
