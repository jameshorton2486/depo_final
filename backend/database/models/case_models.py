from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CaseCreate(BaseModel):
    case_name: str
    caption: str | None = None
    case_style: str | None = None
    cause_number: str | None = None
    venue: str | None = None
    jurisdiction: str | None = None
    district_division: str | None = None
    county: str | None = None
    court_type: str | None = None
    state: str | None = None
    case_status: str = "intake"
    reporting_firm_id: int | None = None
    reporting_firm_office_id: int | None = None
    source_document: str | None = None
    extracted_from: str | None = None
    parser_confidence: float | None = None


class CaseRecord(CaseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
