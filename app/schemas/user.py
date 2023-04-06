from enum import Enum

from pydantic import BaseModel, EmailStr

from app.models.user import TeamRoles


# Shared properties
class UserBase(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = False
    is_superuser: bool = False
    full_name: str | None = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str
    invitation: str | None = None


# Properties to receive via API on update
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    full_name: str | None = None


class UserInDBBase(UserBase):
    id: int | None = None
    team_role: TeamRoles | None = None

    class Config:
        orm_mode = True


class Team(BaseModel):
    id: int
    name: str
    members: list[UserInDBBase]

    class Config:
        orm_mode = True


class PeriodicityEnum(str, Enum):
    monthly = 'monthly'
    annually = 'annually'

# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


# Invitation
class InvitationBase(BaseModel):
    email: EmailStr
    team_id: int
    team_role: TeamRoles | None = None


class Invitation(InvitationBase):
    id: int

    class Config:
        orm_mode = True


class InvitationCreate(InvitationBase):
    pass


class InvitationUpdate(InvitationBase):
    pass
