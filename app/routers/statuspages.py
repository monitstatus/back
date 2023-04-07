from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps


router = APIRouter()
CurrentUser = Annotated[models.User, Depends(deps.get_current_user)]
DBSession = Annotated[Session, Depends(deps.get_db)]


@router.post("/statuspages", response_model=schemas.StatusPage, status_code=status.HTTP_201_CREATED)
async def create_statuspage(
    statuspage: schemas.StatusPageCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    db_existent = crud.statuspage.get_by_subdomain(db, subdomain=statuspage.subdomain)
    if db_existent:
        raise HTTPException(
            status_code=422,
            detail=[{
                'loc': ['body', 'subdomain'],
                'msg': 'A status page with that subdomain already exists',
                'type': 'value_error.str.condition',
            }]
        )

    db_statuspage = crud.statuspage.create_with_owner(
        db=db, obj_in=statuspage, owner_id=current_user.id
    )

    return db_statuspage


@router.get("/statuspages", response_model=list[schemas.StatusPage], status_code=status.HTTP_200_OK)
async def list_statuspages(
    db: DBSession,
    current_user: CurrentUser,
):
    return crud.statuspage.get_multi_by_owner(db, owner_id=current_user.id)


@router.get("/statuspages/{statuspage_id}", response_model=schemas.StatusPage, status_code=status.HTTP_200_OK)
async def get_statuspage(
    statuspage_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    db_statuspage = crud.statuspage.get(db, id=statuspage_id)
    if db_statuspage is None:
        raise HTTPException(status_code=404, detail="Statuspage not found")

    if db_statuspage.owner != current_user:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return db_statuspage


@router.put("/statuspages/{statuspage_id}", response_model=schemas.StatusPage, status_code=status.HTTP_200_OK)
async def update_statuspage(
    statuspage_id: int,
    statuspage: schemas.StatusPageUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    db_statuspage = crud.statuspage.get(db, id=statuspage_id)
    if db_statuspage is None:
        raise HTTPException(status_code=404, detail="Statuspage not found")

    if db_statuspage.owner != current_user:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return crud.statuspage.update(db, db_obj=db_statuspage, obj_in=statuspage)


@router.delete("/statuspages/{statuspage_id}", status_code=status.HTTP_200_OK)
async def delete_statuspage(
    statuspage_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    db_statuspage = crud.statuspage.get(db, id=statuspage_id)
    if db_statuspage is None:
        raise HTTPException(status_code=404, detail="Statuspage not found")

    if db_statuspage.owner != current_user:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return crud.statuspage.remove(db, id=statuspage_id)
