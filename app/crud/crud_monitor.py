from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.monitor import Monitor
from app.schemas.monitor import MonitorCreate, MonitorUpdate


class CRUDMonitor(CRUDBase[Monitor, MonitorCreate, MonitorUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: MonitorCreate, owner_id: int
    ) -> Monitor:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> list[Monitor]:
        return (
            db.query(self.model)
                .filter(Monitor.owner_id == owner_id)
                .order_by(Monitor.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
        )

    def get_multi_by_team(
        self, db: Session, *, team_id: int, skip: int = 0, limit: int = 100
    ) -> list[Monitor]:
        return (
            db.query(self.model)
                .filter(Monitor.owner.has(team_id=team_id))
                .order_by(Monitor.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
        )


monitor = CRUDMonitor(Monitor)
