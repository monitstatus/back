from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.monitor import IncidentEvent
from app.schemas.incident_event import IncidentEventCreate, IncidentEventUpdate


class CRUDIncidentEvent(CRUDBase[IncidentEvent, IncidentEventCreate, IncidentEventUpdate]):
    def get_multi_by_incident(
        self, db: Session, *, incident_id: int
    ) -> list[IncidentEvent]:
        return (
            db.query(self.model)
            .filter(IncidentEvent.incident_id == incident_id)
            .order_by(IncidentEvent.created_at.desc())
            .all()
        )

    def remove_multi_by_monitor(
        self, db: Session, *, monitor_id: int
    ):
        return (
            db.query(self.model)
              .filter(IncidentEvent.incident.has(monitor_id=monitor_id))
              .delete(synchronize_session='fetch')
        )

incident_event = CRUDIncidentEvent(IncidentEvent)
