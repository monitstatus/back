from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app import crud, models, schemas, tasks
from app.api import deps
from app.core import security


router = APIRouter()


@router.post("/users", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(deps.get_db)
):
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="An user with this email already exists",
        )

    user_in.is_superuser = False

    if user_in.invitation:
        user_in.is_active = True
        db_invitation = crud.invitation.get_by_invitation_hash(db, invitation_hash=user_in.invitation)
        # TODO validate email in user is the same in invitation
        user = crud.user.create(db, obj_in=user_in, team_id=db_invitation.team_id)
        crud.invitation.remove(db, id=db_invitation.id)
        return user

    user_in.is_active = False
    user = crud.user.create(db, obj_in=user_in)

    # send account verification email
    token = security.create_access_token(user.id)
    tasks.send_user_verification_mail.delay(user.email, token)

    return user


@router.put("/users", response_model=schemas.User, status_code=status.HTTP_200_OK)
async def update_user(
    user: schemas.UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    return crud.user.update(db, db_obj=current_user, obj_in=user)


@router.delete("/users", status_code=status.HTTP_200_OK)
async def delete_user(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    return crud.user.remove(db, id=current_user.id)


@router.post("/users/invitations", response_model=list[schemas.Invitation], status_code=status.HTTP_201_CREATED)
async def send_invitations(
    emails_in: list[EmailStr],
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    if current_user.team_role != models.user.TeamRoles.owner:
        raise HTTPException(
            status_code=403,
            detail="You must be owner of the team to send invitations"
        )

    # TODO should I do something if a user already exists?
    #      I'm only allowing a user to be in a unique team..
    invitations = []
    for email in emails_in:
        invitation_in = schemas.InvitationCreate(
            email=email,
            team_id=current_user.team_id,
            team_role=models.user.TeamRoles.member,
        )
        invitations.append(
            crud.invitation.create(db, obj_in=invitation_in)
        )

    # queue invitation mails
    for invitation in invitations:
        tasks.send_user_invitation_mail.delay(
          email=invitation.email,
          team_name=invitation.team.name,
          invitation_hash=invitation.invitation_hash,
          invited_by=current_user.full_name,
        )

    return invitations


@router.get("/users/invitations", response_model=list[schemas.Invitation], status_code=status.HTTP_200_OK)
async def list_invitations(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    if current_user.team is None:
        return HTTPException(status_code=403, detail="You don't have a team")

    return crud.invitation.get_by_team_id(db, team_id=current_user.team.id)


@router.delete("/users/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invitation(
    invitation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    if current_user.team is None:
        return HTTPException(status_code=403, detail="You don't have a team")

    db_invitation = crud.invitation.get(db, id=invitation_id)

    if db_invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if db_invitation.team != current_user.team:
        raise HTTPException(status_code=403, detail="Unauthorized")

    crud.invitation.remove(db, id=invitation_id)


@router.delete("/users/team/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_from_team(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    if current_user.team is None:
        return HTTPException(status_code=403, detail="You don't have a team")

    db_user = crud.user.get(db, id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if db_user.team != current_user.team:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if db_user.team_role == models.user.TeamRoles.owner:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if current_user.team_role != models.user.TeamRoles.owner:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # TODO send an email to the user detached?
    crud.user.detach_from_team(db, id=user_id)


@router.post("/users/verify", response_model=schemas.User, status_code=status.HTTP_200_OK)
def verify_user(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    return crud.user.update(db, db_obj=current_user, obj_in={'is_active': True})


@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")

    return {
        "access_token": security.create_access_token(user.id),
        "token_type": "bearer",
    }


@router.post("/login/test-token", response_model=schemas.User)
def test_token(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """ Test access token """
    return current_user
