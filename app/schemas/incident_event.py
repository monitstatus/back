from datetime import datetime
from enum import Enum

from pydantic import BaseModel



class IncidentEventTypeEnum(str, Enum):
    monitoring_failure = 'monitoring_failure'
    monitoring_success = 'monitoring_success'
    alert_sent = 'alert_sent'
    acknowledged = 'acknowledged'


class IncidentEventBase(BaseModel):
    incident_id: int
    type: IncidentEventTypeEnum
    field: str
    extra_field: str | None


class IncidentEventCreate(IncidentEventBase):
    pass


class IncidentEventUpdate(IncidentEventBase):
    pass


class IncidentEvent(IncidentEventBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
