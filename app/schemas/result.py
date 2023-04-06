from datetime import datetime

from pydantic import BaseModel


class ResultBase(BaseModel):
    created_at: datetime
    monitored_at: datetime | None = None
    response_time: float | None = None
    status: bool | None = False
    monitor_id: int


class ResultCreate(ResultBase):
    pass


class ResultUpdate(ResultBase):
    pass


class Result(ResultBase):
    id: int

    class Config:
        orm_mode = True
