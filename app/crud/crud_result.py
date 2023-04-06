from datetime import datetime

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.monitor import Result
from app.schemas.result import ResultCreate, ResultUpdate


class CRUDResult(CRUDBase[Result, ResultCreate, ResultUpdate]):
    def get_multi_by_monitor(
        self, db: Session, *, monitor_id: int, since: datetime = None
    ) -> list[Result]:
        monitor_results = db.query(self.model).filter(Result.monitor_id == monitor_id)

        if since:
            monitor_results = monitor_results.filter(Result.created_at >= since)

        return (
            monitor_results
            .filter(Result.status is not None)
            .order_by(Result.created_at.desc())
            .all()
        )

    def remove_multi_by_monitor(
        self, db: Session, *, monitor_id: int
    ) -> list[Result]:
        return db.query(self.model) \
            .filter(Result.monitor_id == monitor_id) \
            .delete()

    def get_last_by_monitor(self, db: Session, monitor_id: id) -> Result | None:
        return db.query(Result).filter(Result.monitor_id == monitor_id).order_by(Result.created_at.desc()).first()

result = CRUDResult(Result)
