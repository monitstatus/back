from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import case, or_


from app.crud.base import CRUDBase
from app.models.monitor import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate


class CRUDIncident(CRUDBase[Incident, IncidentCreate, IncidentUpdate]):
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[Incident]:
        return db.query(self.model).order_by(Incident.started_at.desc()).offset(skip).limit(limit).all()

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ):
        return (
            db.query(self.model)
            .filter(Incident.monitor.has(owner_id=owner_id))
            .order_by(
                case((Incident.ended_at == None, 0), else_=1),
                Incident.started_at.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_by_monitor(
        self, db: Session, *, monitor_id: int, skip: int = 0, limit: int = 100
    ) -> list[Incident]:
        return (
            db.query(self.model)
            .filter(Incident.monitor_id == monitor_id)
            .order_by(
                case((Incident.ended_at == None, 0), else_=1),
                Incident.started_at.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def remove_multi_by_monitor(
        self, db: Session, *, monitor_id: int
    ) -> list[Incident]:
        return db.query(self.model) \
            .filter(Incident.monitor_id == monitor_id) \
            .delete()

    def get_last_open_by_monitor(self, db: Session, monitor_id: id) -> Incident | None:
        return (
            db.query(self.model)
            .filter(Incident.monitor_id == monitor_id)
            .filter(Incident.ended_at == None)
            .order_by(Incident.started_at.desc())
            .first()
        )

    def get_multi_by_monitor_list_and_date(
        self, db: Session, *, monitor_ids: list[int], since: datetime,
    ) -> list[Incident]:
        """
        Given a list of monitors and a since datetime, return a list of those monitor's incidents,
        either still active or ended at after the specified datetime.
        """
        return (
            db.query(self.model)
            .filter(Incident.monitor_id.in_(monitor_ids))
            .filter(or_(Incident.ended_at == None, Incident.ended_at >= since))
            .order_by(
                case((Incident.ended_at == None, 0), else_=1),
                Incident.started_at.desc()
            )
            .all()
        )


incident = CRUDIncident(Incident)
