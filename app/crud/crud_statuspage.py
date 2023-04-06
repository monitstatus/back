from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.monitor import Monitor
from app.models.statuspage import StatusPage
from app.schemas.statuspage import StatusPageCreate, StatusPageUpdate


class CRUDStatusPage(CRUDBase[StatusPage, StatusPageCreate, StatusPageUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: StatusPageCreate, owner_id: int
    ) -> StatusPage:
        db_obj = self.model(
            company_name=obj_in.company_name,
            subdomain=obj_in.subdomain,
            company_website=obj_in.company_website,
            owner_id=owner_id
        )
        db.add(db_obj)

        monitors = db.query(Monitor) \
            .filter(Monitor.owner_id == owner_id) \
            .filter(Monitor.id.in_(obj_in.monitor_ids))
        db_obj.monitors.extend(monitors)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: StatusPage,
        obj_in: StatusPageUpdate
    ) -> StatusPage:
        db_obj = super().update(db, db_obj=db_obj, obj_in=obj_in)
        monitors = db.query(Monitor).filter(Monitor.id.in_(obj_in.monitor_ids))
        # TODO if monitors list is empty, rollback update and raise exception
        db_obj.monitors = []
        db_obj.monitors.extend(monitors)
        db.commit()
        db.refresh(db_obj)
        return db_obj


    def get_multi_by_owner(
        self, db: Session, *, owner_id: int
    ) -> list[StatusPage]:
        return (
            db.query(self.model)
            .filter(StatusPage.owner_id == owner_id)
            .all()
        )

    def get_by_subdomain(
        self, db: Session, *, subdomain: str
    ) -> StatusPage | None:
        return db.query(StatusPage).filter(StatusPage.subdomain == subdomain).first()


statuspage = CRUDStatusPage(StatusPage)
