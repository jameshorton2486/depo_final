from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CaseCreate(BaseModel):
    case_name: str
    caption: str | None = None
    cause_number: str | None = None
    venue: str | None = None
    jurisdiction: str | None = None
    case_status: str = "intake"
    reporting_firm_id: int | None = None
    reporting_firm_office_id: int | None = None


class CaseRecord(CaseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
