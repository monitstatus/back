from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import DateTime, Float
from sqlalchemy.ext.hybrid import hybrid_property

from app.db.base_class import Base


class Monitor(Base):
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    name = Column(String, nullable=False)
    monitor_type = Column(String, nullable=False, default='http')
    endpoint = Column(String, nullable=False)
    alert_type = Column(String, nullable=False) # TODO maybe enum
    keyword = Column(String)
    periodicity = Column(Integer, nullable=False, default=120)
    request_timeout = Column(Integer, nullable=False, default=30)

    # http requests options
    http_method = Column(String(8), default='GET')
    request_body = Column(String, default=None)
    request_headers = Column(JSON, default=None)
    follow_redirects = Column(Boolean, default=True)
    keep_cookies_between_redirects = Column(Boolean, default=True)
    verify_ssl = Column(Boolean, default=True)
    ssl_check_expiration = Column(Integer, default=0)
    auth_user = Column(String, default=None)
    auth_pass = Column(String, default=None)

    # ping request options
    num_pings = Column(Integer, default=4)

    # tcp / udp options
    port = Column(Integer)
    data = Column(String)

    # alert config
    recovery_period = Column(Integer, default=0)
    confirmation_period = Column(Integer, default=0)
    send_email = Column(Boolean, default=True)

    owner_id = Column(Integer, ForeignKey("user.id"))
    owner = relationship("User", back_populates="monitors")
    results = relationship("Result", back_populates="monitor", cascade="all, delete")
    incidents = relationship("Incident", back_populates="monitor", cascade="all, delete")

    @hybrid_property
    def up(self):
        if self.incidents:
            return self.incidents[-1].ended_at != None

        if self.results:
            if len(self.results) > 1:
                return True
            elif self.results[-1].status != None:
                return self.results[-1].status

        return None

    @hybrid_property
    def status_since(self):
        if self.results:
            if not self.incidents:
                return self.results[0].monitored_at

            if self.incidents[-1].ended_at:
                return self.incidents[-1].ended_at
            else:
                return self.incidents[-1].started_at
        else:
            return None


class Result(Base):
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False)
    monitored_at = Column(DateTime, nullable=True)
    response_time = Column(Float, nullable=True)
    status = Column(Boolean, nullable=True)
    monitor_id = Column(Integer, ForeignKey("monitor.id"))

    monitor = relationship("Monitor", back_populates="results")


class Incident(Base):
    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    monitor_id = Column(Integer, ForeignKey("monitor.id"))
    cause = Column(String, nullable=True)
    request = Column(String, nullable=True)
    response = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("user.id"), nullable=True)

    @hybrid_property
    def monitor_url(self):
        return self.monitor.endpoint

    @hybrid_property
    def monitor_name(self):
        return self.monitor.name

    monitor = relationship("Monitor", back_populates="incidents")
    events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete")


class IncidentEvent(Base):
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incident.id"))
    created_at = Column(DateTime, nullable=False, default=func.now())
    type = Column(String, nullable=False)
    field = Column(String)
    extra_field = Column(String)

    incident = relationship("Incident", back_populates="events")
