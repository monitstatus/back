from datetime import datetime, time
from enum import Enum

from pydantic import BaseModel

from app.models.user import TeamRoles


class RotationTypeEnum(str, Enum):
    daily = 'daily'
    weekly = 'weekly'


class Layer(BaseModel):
    name: str
    rotation_type: RotationTypeEnum | None = RotationTypeEnum.weekly
    start_time: datetime
    handoff_time: time | None
    restriction_day_start: time | None
    restriction_day_end: time | None
    restriction_week_start: datetime | None
    restriction_week_end: datetime | None
    users: list[int]


class User(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    is_superuser: bool
    team_role: TeamRoles

    class Config:
        orm_mode = True


class LayerInDB(Layer):
    users: list[User]

    class Config:
        orm_mode = True
 

class ScheduleBase(BaseModel):
    name: str | None
    layers: list[Layer] | None


class ScheduleCreate(ScheduleBase):
    name: str
    layers: list[Layer]


class ScheduleUpdate(ScheduleBase):
    pass


class Schedule(ScheduleBase):
    id: int
    layers: list[LayerInDB]

    class Config:
        orm_mode = True
