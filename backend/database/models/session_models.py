from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    case_id: int
    session_name: str
    session_date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    location_type: str | None = None
    location_address: str | None = None
    deponent_name: str | None = None
    officer_name: str | None = None
    ordered_by: str | None = None
    service_type: str | None = None
    csr_required: bool = False
    source_document: str | None = None
    extracted_from: str | None = None
    parser_confidence: float | None = None


class SessionRecord(SessionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
