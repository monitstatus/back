from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.user import Customer
from app.schemas.user import CustomerCreate, CustomerUpdate


class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    def get(self, db: Session, id: str) -> Customer | None:
        return db.query(self.model).filter(self.model.stripe_customer_id == id).first()

    def get_by_user_id(self, db: Session, user_id: int) -> Customer | None:
        return db.query(self.model).filter(self.model.user_id == user_id).first()

    def remove(self, db: Session, id: str) -> Customer:
        obj = db.query(self.model).filter(self.model.stripe_customer_id == id).first()
        db.delete(obj)
        db.commit()
        return obj


customer = CRUDCustomer(Customer)
