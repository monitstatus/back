import enum
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

from app.db.base_class import Base
from app.core import config


class TeamRoles(enum.Enum):
    owner = 'owner'
    member = 'member'
    # read_only = 'read_only'


class Invitation(Base):
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    invitation_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    team_role = Column(Enum(TeamRoles), default=TeamRoles.member)
    team_id = Column(Integer, ForeignKey('team.id'))
    team = relationship('Team', back_populates='invitations')


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=False)
    is_superuser = Column(Boolean(), default=False)
    monitors = relationship('Monitor', back_populates='owner')
    integrations = relationship('Integration', back_populates='owner')
    statuspages = relationship('StatusPage', back_populates='owner')
    schedules = relationship('Schedule', back_populates='owner')
    team = relationship('Team', back_populates='members')
    team_role = Column(Enum(TeamRoles), default=TeamRoles.member)
    team_id = Column(Integer, ForeignKey('team.id'))

    def has_access(self, obj):
        if self.team_id:
            return obj.owner.team_id == self.team_id

        return obj.owner == self


class Team(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    members = relationship('User', back_populates='team')
    invitations = relationship('Invitation', back_populates='team')
