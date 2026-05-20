from __future__ import annotations

from backend.entities.keyterms import build_keyterms
from backend.entities.phonetics import generate_phonetic_seeds
from backend.entities.speaker_labels import generate_speaker_label
from backend.parsers.caption_parser import parse_caption
from backend.parsers.nod_parser import parse_nod_text


def process_intake_text(
    text: str, extracted_from: str, intake_metadata: dict[str, object] | None = None
) -> dict[str, object]:
    metadata = intake_metadata or {}
    case_data = parse_caption(text)
    session_data = parse_nod_text(text)

    if metadata.get("case_style"):
        case_data["case_style"] = metadata["case_style"]
    if metadata.get("cause_number"):
        case_data["cause_number"] = metadata["cause_number"]
    if metadata.get("deponent_name"):
        session_data["deponent_name"] = metadata["deponent_name"]

    parties = case_data.pop("parties", [])
    attorneys = session_data.pop("attorneys", [])

    for party in parties:
        party["source_document"] = metadata.get("source_document")
        party["extracted_from"] = extracted_from
        party["parser_confidence"] = 0.86
        party["manual_override"] = False

    for attorney in attorneys:
        attorney["source_document"] = metadata.get("source_document")
        attorney["extracted_from"] = extracted_from
        attorney["parser_confidence"] = 0.82
        attorney["manual_override"] = False
        attorney["speaker_label"] = generate_speaker_label(
            str(attorney.get("full_name", "")),
            honorific=attorney.get("honorific"),
            preserve=attorney.get("speaker_label"),
        )

    case_data.update(
        {
            "source_document": metadata.get("source_document"),
            "extracted_from": extracted_from,
            "parser_confidence": 0.88,
        }
    )
    session_data.update(
        {
            "source_document": metadata.get("source_document"),
            "extracted_from": extracted_from,
            "parser_confidence": 0.83,
        }
    )

    payload = {
        "case": case_data,
        "parties": parties,
        "attorneys": attorneys,
        "session": session_data,
    }
    payload["keyterms"] = build_keyterms(payload)
    payload["phonetics"] = generate_phonetic_seeds(
        [attorney["full_name"] for attorney in attorneys if attorney.get("full_name")],
        (
            metadata.get("phonetic_overrides")
            if isinstance(metadata.get("phonetic_overrides"), dict)
            else {}
        ),
    )
    payload["provenance"] = {
        "source_document": metadata.get("source_document"),
        "extracted_from": extracted_from,
        "parser": "deterministic_regex_pipeline",
    }
    return payload
