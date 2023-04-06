from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
import app.services.availability as availability_services


router = APIRouter()


@router.post("/monitors", response_model=schemas.Monitor, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    monitor: schemas.MonitorCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    # if the alert type is keyword, keyword should be specified
    if monitor.alert_type != schemas.AlertTypeEnum.unavailable and monitor.keyword is None:
        raise HTTPException(
            422,
            [{
                'loc': ["body", 'keyword'],
                'msg': f"should be defined on alert_type {monitor.alert_type.value}",
                'type': 'value_error.str.condition',
            }]
        )

    return crud.monitor.create_with_owner(db=db, obj_in=monitor, owner_id=current_user.id)


@router.get("/monitors", response_model=list[schemas.Monitor], status_code=status.HTTP_200_OK)
async def list_monitors(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    if current_user.team_id:
        return crud.monitor.get_multi_by_team(db, team_id=current_user.team_id)

    return crud.monitor.get_multi_by_owner(db, owner_id=current_user.id)


@router.get("/monitors/{monitor_id}", response_model=schemas.Monitor, status_code=status.HTTP_200_OK)
async def get_monitor(
    monitor_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    db_monitor = crud.monitor.get(db, id=monitor_id)
    if db_monitor is None:
        raise HTTPException(status_code=404, detail="Monitor not found")

    if not current_user.has_access(db_monitor):
        raise HTTPException(status_code=403, detail="Unauthorized")

    return db_monitor


@router.put("/monitors/{monitor_id}", response_model=schemas.Monitor, status_code=status.HTTP_200_OK)
async def update_monitor(
    monitor_id: int,
    monitor: schemas.MonitorUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    db_monitor = crud.monitor.get(db, id=monitor_id)
    if db_monitor is None:
        raise HTTPException(status_code=404, detail="Monitor not found")

    if not current_user.has_access(db_monitor):
        raise HTTPException(status_code=403, detail="Unauthorized")

    return crud.monitor.update(db, db_obj=db_monitor, obj_in=monitor)


@router.delete("/monitors/{monitor_id}", status_code=status.HTTP_200_OK)
async def delete_monitor(
    monitor_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    db_monitor = crud.monitor.get(db, id=monitor_id)
    if db_monitor is None:
        raise HTTPException(status_code=404, detail="Monitor not found")

    if not current_user.has_access(db_monitor):
        raise HTTPException(status_code=403, detail="Unauthorized")

    crud.monitor.remove(db, id=monitor_id)
    return {}


@router.get("/monitors/{monitor_id}/results", response_model=list[schemas.Result], status_code=status.HTTP_200_OK)
async def list_results(
    monitor_id: int,
    since: datetime | None = None,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    # TODO add limit for pagination and avoid enormous queries
    db_monitor = crud.monitor.get(db, id=monitor_id)
    if db_monitor is None:
        raise HTTPException(status_code=404, detail="Monitor not found")

    if not current_user.has_access(db_monitor):
        raise HTTPException(status_code=403, detail="Unauthorized")

    return crud.result.get_multi_by_monitor(db, monitor_id=monitor_id, since=since)


@router.get("/monitors/{monitor_id}/status", status_code=status.HTTP_200_OK)
async def get_monitor_status(
    monitor_id: int,
    start_date: datetime | None = None,
    interval: int = 15,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    if not start_date:
        start_date = datetime.now() - timedelta(days=1)

    db_monitor = crud.monitor.get(db, id=monitor_id)
    if db_monitor is None:
        raise HTTPException(status_code=404, detail="Monitor not found")

    if not current_user.has_access(db_monitor):
        raise HTTPException(status_code=403, detail="Unauthorized")

    results = crud.result.get_multi_by_monitor(db, monitor_id=monitor_id, since=start_date)
    return availability_services.calculate_status_intervals(results, start_date, timedelta(minutes=interval))
