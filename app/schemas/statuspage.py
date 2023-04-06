from pydantic import BaseModel, HttpUrl, validator, conlist


class StatusPageBase(BaseModel):
    company_name: str | None
    subdomain: str | None
    company_website: HttpUrl | None = None
    monitor_ids: conlist(int, min_items=1, unique_items=True)

    @validator('subdomain')
    def validate_not_reserved(cls, v):
        if v in ('', 'www', 'app', 'status'):
            raise ValueError(f"value could not be {v}, its a reserved value")
        return v


class StatusPageCreate(StatusPageBase):
    company_name: str
    subdomain: str
    company_website: HttpUrl | None


class StatusPageUpdate(StatusPageBase):
    pass


class StatusPage(StatusPageBase):
    id: int
    up: bool

    class Config:
        orm_mode = True
