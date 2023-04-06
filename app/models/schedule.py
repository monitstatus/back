from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.sql.sqltypes import DateTime, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


layer_users = Table(
    "layer_users",
    Base.metadata,
    Column("layer_id", ForeignKey("layer.id")),
    Column("user_id", ForeignKey("user.id")),
)


class Layer(Base):
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedule.id", ondelete="CASCADE"))
    schedule = relationship("Schedule", back_populates="layers")
    name = Column(String)
    rotation_type = Column(String, nullable=False, default='weekly')
    start_time = Column(DateTime)
    handoff_time = Column(Time)
    restriction_day_start = Column(Time)
    restriction_day_end = Column(Time)
    restriction_week_start = Column(DateTime)
    restriction_week_end = Column(DateTime)
    users = relationship("User", secondary=layer_users)


class Schedule(Base):
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("user.id"))
    owner = relationship("User", back_populates="schedules")
    created_at = Column(DateTime, default=func.now())
    name = Column(String, nullable=False)
    layers = relationship(
        "Layer",
        back_populates="schedule",
        cascade="all, delete",
        passive_deletes=True,
    )
