from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()


@router.get("/incidents", response_model=list[schemas.Incident], status_code=status.HTTP_200_OK)
async def list_incidents(
    monitor_id: int | None = None,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    if monitor_id:
        db_monitor = crud.monitor.get(db, id=monitor_id)
        if db_monitor is None:
            raise HTTPException(status_code=404, detail="Monitor not found")

        if not current_user.has_access(db_monitor):
            raise HTTPException(status_code=403, detail="Unauthorized")

        return crud.incident.get_multi_by_monitor(db, monitor_id=monitor_id)

    return crud.incident.get_multi_by_owner(db, owner_id=current_user.id)


@router.get("/incidents/{incident_id}", response_model=schemas.Incident, status_code=status.HTTP_200_OK)
async def get_incident(
    incident_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    db_incident = crud.incident.get(db, id=incident_id)
    if db_incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    if not current_user.has_access(db_incident.monitor):
        raise HTTPException(status_code=403, detail="Unauthorized")

    return db_incident


@router.get("/incidents/{incident_id}/events", response_model=list[schemas.IncidentEvent], status_code=status.HTTP_200_OK)
async def get_incident_events(
    incident_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    db_incident = crud.incident.get(db, id=incident_id)
    if db_incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    if not current_user.has_access(db_incident.monitor):
        raise HTTPException(status_code=403, detail="Unauthorized")

    return crud.incident_event.get_multi_by_incident(db, incident_id=db_incident.id)


@router.post("/incidents/{incident_id}/acknowledge", response_model=schemas.Incident, status_code=status.HTTP_200_OK)
async def acknowledge_incident(
    incident_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    db_incident = crud.incident.get(db, id=incident_id)
    if db_incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    if not current_user.has_access(db_incident.monitor):
        raise HTTPException(status_code=403, detail="Unauthorized")

    if db_incident.acknowledged_at:
        raise HTTPException(status_code=400, detail="Incident already acknowledged")

    # update incident acknowledged fields
    incident_update = schemas.IncidentUpdate(
        acknowledged_at=datetime.now(),
        acknowledged_by=current_user.id,
    )
    updated_incident = crud.incident.update(db, db_obj=db_incident, obj_in=incident_update)

    # create an incident event representing the acknowledgement
    crud.incident_event.create(db, obj_in=schemas.IncidentEventCreate(
        incident_id=db_incident.id,
        type=schemas.IncidentEventTypeEnum.acknowledged,
        field=current_user.full_name,
    ))

    return updated_incident