from __future__ import annotations

from collections import OrderedDict

DEFAULT_LEGAL_TERMS = [
    ("deposition", "legal_term", 0.7, "legal_term"),
    ("court reporter", "legal_term", 0.7, "legal_term"),
    ("notice of deposition", "legal_term", 0.75, "legal_term"),
]


def build_keyterms(payload: dict[str, object]) -> dict[str, object]:
    ordered: "OrderedDict[str, dict[str, object]]" = OrderedDict()

    def add_term(term: str | None, category: str, weight: float, source: str) -> None:
        if not term:
            return
        cleaned = str(term).strip()
        if len(cleaned) < 2:
            return
        key = cleaned.lower()
        if key not in ordered:
            ordered[key] = {
                "term": cleaned,
                "category": category,
                "weight": weight,
                "source": source,
            }

    case_data = payload.get("case", {})
    if isinstance(case_data, dict):
        add_term(case_data.get("case_style"), "organization", 1.4, "case_style")
        add_term(case_data.get("cause_number"), "acronym", 0.9, "cause_number")
        add_term(case_data.get("district_division"), "legal_term", 0.8, "court")
        add_term(case_data.get("county"), "address", 0.7, "county")

    for party in payload.get("parties", []):
        if isinstance(party, dict):
            category = (
                "organization"
                if party.get("entity_type") in {"corporation", "llc", "gov"}
                else "witness"
            )
            add_term(party.get("party_name"), category, 1.35, "party")
            add_term(party.get("alias_name"), category, 1.1, "party_alias")

    for attorney in payload.get("attorneys", []):
        if isinstance(attorney, dict):
            add_term(attorney.get("full_name"), "attorney", 1.25, "attorney")
            add_term(attorney.get("law_firm"), "law_firm", 1.1, "law_firm")
            add_term(attorney.get("email"), "email", 0.85, "email")
            address = attorney.get("address_line_1")
            if address:
                add_term(address, "address", 0.85, "address")

    session_data = payload.get("session", {})
    if isinstance(session_data, dict):
        add_term(session_data.get("deponent_name"), "witness", 1.5, "deponent")
        add_term(session_data.get("location_address"), "address", 0.8, "location")

    for term, category, weight, source in DEFAULT_LEGAL_TERMS:
        add_term(term, category, weight, source)

    keyterms = list(ordered.values())[:100]
    return {
        "term_count": len(keyterms),
        "truncated": len(ordered) > 100,
        "keyterms": keyterms,
    }
