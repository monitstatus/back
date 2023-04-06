import secrets

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user import Invitation
from app.schemas.user import InvitationCreate, InvitationUpdate


class CRUDInvitation(CRUDBase[Invitation, InvitationCreate, InvitationUpdate]):
    def create(self, db: Session, *, obj_in: InvitationCreate) -> Invitation:
        db_obj = Invitation(
            email=obj_in.email,
            invitation_hash=secrets.token_urlsafe(32),
            team_role=obj_in.team_role,
            team_id=obj_in.team_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_email(self, db: Session, *, email: str) -> Invitation | None:
        return db.query(Invitation).filter(Invitation.email == email).first()

    def get_by_team_id(self, db: Session, *, team_id: int) -> list[Invitation]:
        return db.query(Invitation).filter(Invitation.team_id == team_id).all()

    def get_by_invitation_hash(self, db: Session, *, invitation_hash: str) -> Invitation | None:
        return db.query(Invitation).filter(Invitation.invitation_hash == invitation_hash).first()


invitation = CRUDInvitation(Invitation)
