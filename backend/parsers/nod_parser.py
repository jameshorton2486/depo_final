from __future__ import annotations

import re

from backend.entities.addresses import extract_addresses
from backend.entities.attorneys import extract_attorneys
from backend.entities.parser_utils import normalize_whitespace, parse_date_string

DATE_RE = re.compile(r"(?:Date|Dated)\s*[:\-]?\s*([A-Za-z0-9, /]+)", re.IGNORECASE)
TIME_RE = re.compile(r"(?:Time)\s*[:\-]?\s*([0-9: ]+(?:AM|PM))", re.IGNORECASE)
DEPONENT_RE = re.compile(
    r"(?:Deponent|deposition of)\s*[:\-]?\s*([A-Z][A-Za-z .'-]+?)(?:\s+will\b|\s+to\b|[\n.,]|$)",
    re.IGNORECASE,
)
ORDERED_BY_RE = re.compile(r"Ordered by\s*[:\-]?\s*([A-Z][A-Za-z .'-]+)", re.IGNORECASE)


def parse_nod_text(text: str) -> dict[str, object]:
    normalized = normalize_whitespace(text)
    addresses = extract_addresses(text)
    location_type = (
        "zoom" if "zoom" in normalized.lower() or "remote" in normalized.lower() else "in_person"
    )
    location_address = addresses[0]["address_line_1"] if addresses else None
    session_date = None
    date_match = DATE_RE.search(text)
    if date_match:
        session_date = parse_date_string(date_match.group(1))
    time_match = TIME_RE.search(text)
    deponent_match = DEPONENT_RE.search(text)
    ordered_by_match = ORDERED_BY_RE.search(text)
    return {
        "session_name": "Deposition Intake Session",
        "session_date": session_date,
        "start_time": time_match.group(1).strip() if time_match else None,
        "location": location_address or ("Remote / Zoom" if location_type == "zoom" else None),
        "location_type": location_type,
        "location_address": location_address,
        "deponent_name": deponent_match.group(1).strip() if deponent_match else None,
        "ordered_by": ordered_by_match.group(1).strip() if ordered_by_match else None,
        "service_type": "CR_plus_Zoom" if location_type == "zoom" else "CR_only",
        "csr_required": "court reporter" in normalized.lower() or "csr" in normalized.lower(),
        "attorneys": extract_attorneys(text),
    }
