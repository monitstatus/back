from datetime import datetime

from pydantic import BaseModel


class IncidentBase(BaseModel):
    started_at: datetime | None
    ended_at: datetime | None = None
    monitor_id: int
    cause: str | None = None
    request: str | None = None
    response: str | None = None
    acknowledged_by: int | None = None
    acknowledged_at: datetime | None = None


class IncidentCreate(IncidentBase):
    started_at: datetime


class IncidentUpdate(IncidentBase):
    monitor_id: int | None

class Incident(IncidentBase):
    id: int
    monitor_url: str
    monitor_name: str

    class Config:
        orm_mode = True
