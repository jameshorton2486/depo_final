from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from backend.database.init_db import initialize_database
from backend.database.models.case_models import CaseCreate
from backend.database.models.session_models import SessionCreate
from backend.database.repositories.cases_repo import (
    create_case,
    get_case_intake,
    replace_case_attorneys,
    replace_case_parties,
    update_case,
)
from backend.database.repositories.sessions_repo import create_session, list_sessions_for_case
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
        "keyterms": keyterm_payload | {"file_path": str(keyterms_path)},
        "phonetics": phonetics_payload | {"file_path": str(phonetics_path)},
        "provenance": parsed["provenance"],
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
    return {
        **bundle,
        "sessions": sessions,
        "keyterms": keyterms,
        "phonetics": phonetics,
    }


def _read_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
