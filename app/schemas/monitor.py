from datetime import datetime
from enum import Enum
from typing import Dict

from pydantic import BaseModel


class MonitorTypeEnum(str, Enum):
    http = 'http'
    ping = 'ping'
    tcp = 'tcp'
    udp = 'udp'


class AlertTypeEnum(str, Enum):
    unavailable = 'unavailable'
    contains_keyword = 'contains_keyword'
    does_not_contain_keyword = 'does_not_contain_keyword'


class HTTPMethodEnum(str, Enum):
    get = 'GET'
    post = 'POST'
    head = 'HEAD'


class MonitorBase(BaseModel):
    name: str | None
    monitor_type: MonitorTypeEnum | None = MonitorTypeEnum.http
    endpoint: str | None
    alert_type: AlertTypeEnum | None = AlertTypeEnum.unavailable
    keyword: str | None = None
    periodicity: int | None = 120
    request_timeout: int | None = 30

    # http requests options
    http_method: HTTPMethodEnum | None = HTTPMethodEnum.get
    request_body: str | None = None
    request_headers: Dict[str, str] | None = None
    follow_redirects: bool | None = True
    keep_cookies_between_redirects: bool | None = True
    verify_ssl: bool | None = True
    ssl_check_expiration: int | None = None
    auth_user: str | None = None
    auth_pass: str | None = None

    # pring request options
    num_pings: int | None = 4

    # tcp / udp options
    port: int | None = None
    data: str | None = None

    # alert config
    recovery_period: int | None = 0
    confirmation_period: int | None = 0
    send_email: bool | None = True

    class Config:
        schema_extra = {
            "example": {
                "name": "My monitor name",
                "monitor_type": "http",
                "endpoint": "https://www.google.com",
                "alert_type": "contains_keyword",
                "keyword": "Google",
            }
        }


class MonitorCreate(MonitorBase):
    name: str
    endpoint: str


class MonitorUpdate(MonitorBase):
    pass


class Monitor(MonitorBase):
    id: int
    up: bool | None = None
    status_since: datetime | None = None

    class Config:
        orm_mode = True
