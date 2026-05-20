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
    deponent_name: str | None = None
    officer_name: str | None = None


class SessionRecord(SessionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
