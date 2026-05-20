from __future__ import annotations

from backend.database.models.case_models import CaseRecord
from backend.database.models.session_models import SessionRecord


def build_certificate_page(case_record: CaseRecord, session_record: SessionRecord) -> list[str]:
    witness_name = session_record.deponent_name or "the witness"
    return [
        "COURT REPORTER CERTIFICATE",
        "",
        f"Cause No.: {case_record.cause_number or 'Not provided'}",
        f"Style: {case_record.case_style or case_record.case_name}",
        f"Session: {session_record.session_name}",
        f"Witness: {witness_name}",
        "",
        "I certify that the foregoing transcript was reduced from the canonical deposition",
        "record maintained in DEPO-PRO and rendered without altering the substantive testimony.",
        "",
        "Read & Sign: ____________________",
        "Court Reporter: ____________________",
        "CNA Certificate Foundation: ____________________",
    ]
