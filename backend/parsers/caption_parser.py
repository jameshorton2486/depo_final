from __future__ import annotations

from backend.entities.parser_utils import non_empty_lines
from backend.entities.parties import extract_case_and_parties


def parse_caption(text: str) -> dict[str, object]:
    parsed = extract_case_and_parties(text)
    lines = non_empty_lines(text)
    district_division = next(
        (line for line in lines if "division" in line.lower() or "district" in line.lower()),
        None,
    )
    county = next((line for line in lines if "county" in line.lower()), None)
    jurisdiction = "federal" if "united states district court" in text.lower() else "texas_state"
    court_type = "federal_district" if jurisdiction == "federal" else "state_district"
    return {
        "case_style": parsed.get("case_style"),
        "cause_number": parsed.get("cause_number"),
        "district_division": district_division,
        "county": county,
        "jurisdiction": jurisdiction,
        "court_type": court_type,
        "parties": parsed.get("parties", []),
        "case_name": parsed.get("case_style") or "Untitled Intake Matter",
        "caption": parsed.get("case_style"),
        "venue": county or district_division,
        "state": "Texas",
    }
