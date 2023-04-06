from sqlalchemy.orm import Session

from app import crud
from app.models.user import User


def user_has_arrived_to_max_monitors_in_plan(db: Session, current_user: User):
    user_id = current_user.id
    customer = crud.customer.get_by_user_id(db, user_id=user_id)

    # TODO validate by team?
    monitors = crud.monitor.get_multi_by_owner(db, owner_id=user_id)

    return len(monitors) >= customer.max_monitors


def user_plan_allows_periodicity(db: Session, current_user: User, periodicity: int):
    user_id = current_user.id
    customer = crud.customer.get_by_user_id(db, user_id=user_id)

    # TODO also validate by team, if user is in a team and customer is associated with the team owner

    return periodicity >= customer.min_check_interval
