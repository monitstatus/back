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


class Customer(Base):
    stripe_customer_id = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    plan_price_id = Column(String)

    @hybrid_property
    def tier(self):
        if self.plan_price_id in (config.STRIPE_BASIC_MONTHLY_PRICE_ID, config.STRIPE_BASIC_ANNUALLY_PRICE_ID):
            return 'basic'
        elif self.plan_price_id in (config.STRIPE_STARTUP_MONTHLY_PRICE_ID, config.STRIPE_STARTUP_ANNUALLY_PRICE_ID):
            return 'startup'
        elif self.plan_price_id in (config.STRIPE_ENTERPRISE_MONTHLY_PRICE_ID, config.STRIPE_ENTERPRISE_ANNUALLY_PRICE_ID):
            return 'enterprise'
        else:
            return None

    @hybrid_property
    def periodicity(self):
        if self.plan_price_id in (config.STRIPE_BASIC_MONTHLY_PRICE_ID, config.STRIPE_STARTUP_MONTHLY_PRICE_ID, config.STRIPE_ENTERPRISE_MONTHLY_PRICE_ID):
            return 'monthly'
        elif self.plan_price_id in (config.STRIPE_BASIC_ANNUALLY_PRICE_ID, config.STRIPE_STARTUP_ANNUALLY_PRICE_ID, config.STRIPE_ENTERPRISE_ANNUALLY_PRICE_ID):
            return 'annually'
        else:
            return None

    @hybrid_property
    def max_monitors(self):
        if self.tier == 'startup':
            return 50
        elif self.tier == 'enterprise':
            return 100

        return 10

    @hybrid_property
    def min_check_interval(self):
        if self.tier == 'startup':
            return 60
        elif self.tier == 'enterprise':
            return 30

        return 120

    @hybrid_property
    def max_locations(self):
        if self.tier == 'startup':
            return 3
        elif self.tier == 'enterprise':
            return 5

        return 1

    @hybrid_property
    def max_team_users(self):
        if self.tier == 'startup':
            return 3
        elif self.tier == 'enterprise':
            return 8

        return 1
