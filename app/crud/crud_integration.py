from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.integration import Integration
from app.schemas.integration import IntegrationCreate, IntegrationUpdate


class CRUDIntegration(CRUDBase[Integration, IntegrationCreate, IntegrationUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: IntegrationCreate, owner_id: int
    ) -> Integration:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_telegram_random_string(
        self, db: Session, *, telegram_random_string: str
    ) -> Integration:
        return (
            db.query(self.model)
            .filter(Integration.telegram_random_string == telegram_random_string)
            .first()
        )

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> list[Integration]:
        return (
            db.query(self.model)
            .filter(Integration.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


integration = CRUDIntegration(Integration)
