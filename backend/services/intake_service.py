from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from backend.database.init_db import initialize_database
from backend.database.models.case_models import CaseCreate
from backend.database.models.session_models import SessionCreate
from backend.database.repositories.cases_repo import (
    create_case,
    get_case_intake,
    list_cases,
    replace_case_attorneys,
    replace_case_parties,
    update_case,
)
from backend.database.repositories.sessions_repo import create_session, list_sessions_for_case
from backend.entities.speaker_labels import generate_speaker_label
from backend.parsers.intake_pipeline import run_intake_pipeline
from backend.services.keyterm_service import write_keyterms
from backend.services.speaker_service import write_phonetics


class IntakeParseRequest(BaseModel):
    case_id: int | None = None
    file_name: str | None = None
    file_content_base64: str | None = None
    pasted_text: str | None = None
    intake_metadata: dict[str, object] = Field(default_factory=dict)


def parse_and_persist(
    request: IntakeParseRequest, database_path: Path | None = None
) -> dict[str, object]:
    initialize_database(database_path)
    parsed = run_intake_pipeline(
        pasted_text=request.pasted_text,
        file_name=request.file_name,
        file_content_base64=request.file_content_base64,
        intake_metadata=request.intake_metadata,
    )
    case_payload = CaseCreate(
        case_name=str(
            parsed["case"].get("case_name")
            or parsed["case"].get("case_style")
            or "Untitled Intake Matter"
        ),
        caption=parsed["case"].get("caption"),
        case_style=parsed["case"].get("case_style"),
        cause_number=parsed["case"].get("cause_number"),
        venue=parsed["case"].get("venue"),
        jurisdiction=parsed["case"].get("jurisdiction"),
        district_division=parsed["case"].get("district_division"),
        county=parsed["case"].get("county"),
        court_type=parsed["case"].get("court_type"),
        state=parsed["case"].get("state"),
        source_document=parsed["case"].get("source_document"),
        extracted_from=parsed["case"].get("extracted_from"),
        parser_confidence=parsed["case"].get("parser_confidence"),
    )
    if request.case_id:
        case_record = update_case(
            request.case_id, case_payload.model_dump(exclude={"case_name"}), database_path
        )
    else:
        case_record = create_case(case_payload, database_path)

    created_parties = replace_case_parties(case_record.id, parsed["parties"], database_path)
    created_attorneys = replace_case_attorneys(case_record.id, parsed["attorneys"], database_path)
    session_record = create_session(
        SessionCreate(case_id=case_record.id, **parsed["session"]),
        database_path,
    )

    keyterm_payload = {
        "case_id": case_record.id,
        "case_caption": parsed["case"].get("case_style"),
        "cause_number": parsed["case"].get("cause_number"),
        "source": "intake_pipeline",
        **parsed["keyterms"],
    }
    phonetics_payload = {
        "case_id": case_record.id,
        "source": "intake_pipeline",
        **parsed["phonetics"],
    }
    keyterms_path = write_keyterms(case_record.id, keyterm_payload)
    phonetics_path = write_phonetics(case_record.id, phonetics_payload)

    return {
        "case_id": case_record.id,
        "case": case_record.model_dump(mode="json"),
        "parties": created_parties,
        "attorneys": created_attorneys,
        "session": session_record.model_dump(mode="json"),
        "keyterms": keyterm_payload | _file_metadata(keyterms_path),
        "phonetics": phonetics_payload | _file_metadata(phonetics_path),
        "provenance": parsed["provenance"],
        "speaker_labels": _build_speaker_labels(
            created_attorneys, session_record.model_dump(mode="json")
        ),
        "case_state": _build_case_state(
            case_record.model_dump(mode="json"), [session_record.model_dump(mode="json")]
        ),
        "provenance_entries": _build_provenance_entries(
            case_record.model_dump(mode="json"),
            created_parties,
            created_attorneys,
            session_record.model_dump(mode="json"),
        ),
    }


def get_intake(case_id: int, database_path: Path | None = None) -> dict[str, object]:
    bundle = get_case_intake(case_id, database_path)
    sessions = [
        session.model_dump(mode="json")
        for session in list_sessions_for_case(case_id, database_path)
    ]
    case_dir = Path("data") / "cases" / str(case_id)
    keyterms = _read_json(case_dir / "keyterms.json")
    phonetics = _read_json(case_dir / "phonetics.json")
    case_state = _build_case_state(bundle["case"], sessions)
    return {
        **bundle,
        "sessions": sessions,
        "keyterms": _decorate_json_payload(case_dir / "keyterms.json", keyterms),
        "phonetics": _decorate_json_payload(case_dir / "phonetics.json", phonetics),
        "speaker_labels": _build_speaker_labels(
            bundle.get("attorneys", []), sessions[0] if sessions else None
        ),
        "provenance_entries": _build_provenance_entries(
            bundle["case"],
            bundle.get("parties", []),
            bundle.get("attorneys", []),
            sessions[0] if sessions else None,
        ),
        "case_state": case_state,
    }


def list_intake_cases(database_path: Path | None = None) -> dict[str, object]:
    initialize_database(database_path)
    items: list[dict[str, object]] = []
    for case_record in list_cases(database_path):
        sessions = [
            session.model_dump(mode="json")
            for session in list_sessions_for_case(case_record.id, database_path)
        ]
        items.append(
            {
                "case": case_record.model_dump(mode="json"),
                "case_state": _build_case_state(case_record.model_dump(mode="json"), sessions),
                "session_count": len(sessions),
                "latest_session_id": sessions[-1]["id"] if sessions else None,
                "latest_session_name": sessions[-1]["session_name"] if sessions else None,
            }
        )
    return {"items": items}


def update_case_stage(
    case_id: int,
    stage_id: int,
    database_path: Path | None = None,
) -> dict[str, object]:
    initialize_database(database_path)
    case_record = update_case(case_id, {"case_status": _stage_key(stage_id)}, database_path)
    sessions = [
        session.model_dump(mode="json")
        for session in list_sessions_for_case(case_id, database_path)
    ]
    return {
        "case": case_record.model_dump(mode="json"),
        "case_state": _build_case_state(case_record.model_dump(mode="json"), sessions),
    }


def _read_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _build_case_state(
    case_data: dict[str, object], sessions: list[dict[str, object]]
) -> dict[str, object]:
    stage_key = str(case_data.get("case_status") or "intake")
    stage_id = _stage_id(stage_key)
    completed_stage_ids = list(range(1, stage_id))
    latest_session_id = sessions[-1]["id"] if sessions else None
    return {
        "stage_id": stage_id,
        "stage_key": stage_key,
        "stage_label": stage_key.replace("_", " ").title(),
        "session_count": len(sessions),
        "latest_session_id": latest_session_id,
        "is_export_ready": bool(latest_session_id and stage_id >= 6),
        "review_state": "ready" if latest_session_id and stage_id >= 3 else "pending",
        "completed_stage_ids": completed_stage_ids,
    }


def _stage_id(stage_key: str) -> int:
    mapping = {
        "intake": 1,
        "transcripts": 2,
        "workspace": 3,
        "insertions": 4,
        "certify": 5,
        "export": 6,
    }
    return mapping.get(stage_key, 1)


def _stage_key(stage_id: int) -> str:
    mapping = {
        1: "intake",
        2: "transcripts",
        3: "workspace",
        4: "insertions",
        5: "certify",
        6: "export",
    }
    return mapping.get(stage_id, "intake")


def _build_speaker_labels(
    attorneys: list[dict[str, object]],
    session_data: dict[str, object] | None,
) -> list[dict[str, object]]:
    labels: list[dict[str, object]] = []
    for entry in attorneys:
        attorney_data = entry.get("attorney", entry)
        case_attorney = entry.get("case_attorney", {})
        labels.append(
            {
                "speaker_label": case_attorney.get("speaker_label") or "Ambiguous",
                "full_name": attorney_data.get("full_name"),
                "role": "attorney",
                "source": case_attorney.get("extracted_from")
                or attorney_data.get("extracted_from"),
                "confidence": case_attorney.get("parser_confidence")
                or attorney_data.get("parser_confidence"),
            }
        )
    if session_data and session_data.get("deponent_name"):
        labels.append(
            {
                "speaker_label": generate_speaker_label(str(session_data["deponent_name"]))
                or "WITNESS",
                "full_name": session_data["deponent_name"],
                "role": "witness",
                "source": session_data.get("extracted_from"),
                "confidence": session_data.get("parser_confidence"),
            }
        )
    labels.append(
        {
            "speaker_label": "THE REPORTER",
            "full_name": "Court Reporter",
            "role": "reporter",
            "source": "system",
            "confidence": 1.0,
        }
    )
    labels.append(
        {
            "speaker_label": "THE INTERPRETER",
            "full_name": "Interpreter",
            "role": "interpreter",
            "source": "system",
            "confidence": 1.0,
        }
    )
    seen: set[str] = set()
    deduped: list[dict[str, object]] = []
    for item in labels:
        key = str(item["speaker_label"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _build_provenance_entries(
    case_data: dict[str, object],
    parties: list[dict[str, object]],
    attorneys: list[dict[str, object]],
    session_data: dict[str, object] | None,
) -> list[dict[str, object]]:
    entries = [
        {
            "label": "Case Metadata",
            "source_document": case_data.get("source_document"),
            "extracted_from": case_data.get("extracted_from"),
            "parser_confidence": case_data.get("parser_confidence"),
            "manual_override": False,
            "timestamp": case_data.get("updated_at") or case_data.get("created_at"),
        }
    ]
    if session_data:
        entries.append(
            {
                "label": "Session Metadata",
                "source_document": session_data.get("source_document"),
                "extracted_from": session_data.get("extracted_from"),
                "parser_confidence": session_data.get("parser_confidence"),
                "manual_override": False,
                "timestamp": session_data.get("created_at"),
            }
        )
    for party in parties[:3]:
        entries.append(
            {
                "label": f"Party: {party.get('party_name')}",
                "source_document": party.get("source_document"),
                "extracted_from": party.get("extracted_from"),
                "parser_confidence": party.get("parser_confidence"),
                "manual_override": bool(party.get("manual_override")),
                "timestamp": party.get("created_at"),
            }
        )
    for entry in attorneys[:3]:
        attorney_data = entry.get("attorney", entry)
        case_attorney = entry.get("case_attorney", {})
        entries.append(
            {
                "label": f"Attorney: {attorney_data.get('full_name')}",
                "source_document": attorney_data.get("source_document"),
                "extracted_from": case_attorney.get("extracted_from")
                or attorney_data.get("extracted_from"),
                "parser_confidence": case_attorney.get("parser_confidence")
                or attorney_data.get("parser_confidence"),
                "manual_override": bool(
                    case_attorney.get("manual_override") or attorney_data.get("manual_override")
                ),
                "timestamp": attorney_data.get("created_at"),
            }
        )
    return entries


def _file_metadata(path: Path) -> dict[str, object]:
    timestamp = datetime.fromtimestamp(path.stat().st_mtime).isoformat() if path.exists() else None
    return {"file_path": str(path), "generated_at": timestamp}


def _decorate_json_payload(
    path: Path, payload: dict[str, object] | None
) -> dict[str, object] | None:
    if payload is None:
        return None
    return payload | _file_metadata(path)
