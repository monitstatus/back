from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()
CurrentUser = Annotated[models.User, Depends(deps.get_current_user)]
DBSession = Annotated[Session, Depends(deps.get_db)]


@router.post("/schedules", response_model=schemas.Schedule, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule: schemas.ScheduleCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    # TODO validate that users are in the same team that the schedule owner! VULNERABILITY
    db_obj = crud.schedule.create_with_owner(db=db, obj_in=schedule, owner_id=current_user.id)
    return db_obj


@router.get("/schedules", response_model=list[schemas.Schedule], status_code=status.HTTP_200_OK)
async def list_schedules(
    db: DBSession,
    current_user: CurrentUser,
):
    #if current_user.team_id:
    #    return crud.schedule.get_multi_by_team(db, team_id=current_user.team_id)

    return crud.schedule.get_multi_by_owner(db, owner_id=current_user.id)


@router.get("/schedules/{schedule_id}", response_model=schemas.Schedule, status_code=status.HTTP_200_OK)
async def get_schedule(
    schedule_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    db_schedule = crud.schedule.get(db, id=schedule_id)

    if db_schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if not current_user.has_access(db_schedule):
        raise HTTPException(status_code=403, detail="Unauthorized")

    return db_schedule


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    db_schedule = crud.schedule.get(db, id=schedule_id)

    if db_schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if not current_user.has_access(db_schedule):
        raise HTTPException(status_code=403, detail="Unauthorized")

    crud.schedule.remove(db, id=schedule_id)
    return {}

@router.put("/schedules/{schedule_id}", response_model=schemas.Schedule, status_code=status.HTTP_200_OK)
async def update_schedule(
    schedule_id: int,
    schedule: schemas.ScheduleUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    db_schedule = crud.schedule.get(db, id=schedule_id)

    if db_schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if not current_user.has_access(db_schedule):
        raise HTTPException(status_code=403, detail="Unauthorized")

    return crud.schedule.update(db, db_obj=db_schedule, obj_in=schedule)
