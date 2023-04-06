from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.crud_user import user as crud_user
from app.crud.base import CRUDBase
from app.models.schedule import Schedule, Layer
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


class CRUDSchedule(CRUDBase[Schedule, ScheduleCreate, ScheduleUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: ScheduleCreate, owner_id: int
    ) -> Schedule:
        obj_in_data = jsonable_encoder(obj_in)
        schedule_obj = self.model(name=obj_in_data['name'], owner_id=owner_id)
        db.add(schedule_obj)
        db.commit()
        db.refresh(schedule_obj)

        for layer in obj_in.layers:
            layer_obj = Layer(
                schedule_id=schedule_obj.id,
                name=layer.name,
                rotation_type=layer.rotation_type,
                start_time=layer.start_time,
                handoff_time=layer.handoff_time,
                restriction_day_start = layer.restriction_day_start,
                restriction_day_end = layer.restriction_day_end,
                restriction_week_start = layer.restriction_week_start,
                restriction_week_end = layer.restriction_week_end,
            )
            for user_id in layer.users:
                user_obj = crud_user.get(db=db, id=user_id)
                layer_obj.users.append(user_obj)

            schedule_obj.layers.append(layer_obj)
        db.commit()
        db.refresh(schedule_obj)
        return schedule_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Schedule,
        obj_in: ScheduleUpdate  #| Dict[str, Any]
    ) -> Schedule:
        if obj_in.name:
            db_obj.name = obj_in.name

        if obj_in.layers:
            db_obj.layers = []
            for layer in obj_in.layers:
                layer_obj = Layer(
                    schedule_id=db_obj.id,
                    name=layer.name,
                    rotation_type=layer.rotation_type,
                    start_time=layer.start_time,
                    handoff_time=layer.handoff_time,
                    restriction_day_start = layer.restriction_day_start,
                    restriction_day_end = layer.restriction_day_end,
                    restriction_week_start = layer.restriction_week_start,
                    restriction_week_end = layer.restriction_week_end,
                )
                for user_id in layer.users:
                    user_obj = crud_user.get(db=db, id=user_id)
                    layer_obj.users.append(user_obj)

                db_obj.layers.append(layer_obj)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> list[Schedule]:
        return db.query(self.model).filter(self.model.owner_id == owner_id).all()

    def get_multi_by_team(
        self, db: Session, *, team_id: int, skip: int = 0, limit: int = 100
    ) -> list[Schedule]:
        return db.query(self.model).filter(self.model.owner.team_id == team_id).all()

    def remove(
        self, db: Session, *, id: int
    ) -> Schedule:
        schedule_layers = db.query(Layer).filter(Layer.schedule_id == id).all()
        for layer in schedule_layers:
            layer.users = []

        schedule = db.query(Schedule).get(id)
        db.delete(schedule)
        db.commit()
        return schedule

schedule = CRUDSchedule(Schedule)
