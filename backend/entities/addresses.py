from __future__ import annotations

import re

from backend.entities.parser_utils import non_empty_lines

ADDRESS_RE = re.compile(
    r"\d{2,6}\s+[A-Za-z0-9.#'\- ]+(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Highway|Hwy\.?|"
    r"Drive|Dr\.?|Place|Pl\.?|Boulevard|Blvd\.?|Suite|Ste\.?|Way|Lane|Ln\.?)",
    re.IGNORECASE,
)
CITY_STATE_ZIP_RE = re.compile(r"([A-Za-z .'-]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)")


def extract_addresses(text: str) -> list[dict[str, str | None]]:
    addresses: list[dict[str, str | None]] = []
    lines = non_empty_lines(text)
    for index, line in enumerate(lines):
        if not ADDRESS_RE.search(line):
            continue
        city = state = postal_code = None
        if index + 1 < len(lines):
            match = CITY_STATE_ZIP_RE.search(lines[index + 1])
            if match:
                city, state, postal_code = match.groups()
        addresses.append(
            {
                "address_line_1": line,
                "city": city,
                "state": state,
                "postal_code": postal_code,
            }
        )
    return addresses
