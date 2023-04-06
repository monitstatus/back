from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas, tasks
from app.api import deps
from app.core import config
from app.services.integrations import generate_random_string


router = APIRouter()


@router.post("/integrations", response_model=schemas.Integration, status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration: schemas.IntegrationCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    if integration.kind == schemas.IntegrationServicesEnum.telegram:
        integration.telegram_random_string = generate_random_string()

    return crud.integration.create_with_owner(db=db, obj_in=integration, owner_id=current_user.id)


@router.get("/integrations", response_model=list[schemas.Integration], status_code=status.HTTP_200_OK)
async def list_integrations(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    return crud.integration.get_multi_by_owner(db, owner_id=current_user.id)


@router.delete("/integrations/{integration_id}", status_code=status.HTTP_200_OK)
async def delete_integration(
    integration_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    db_integration = crud.integration.get(db, id=integration_id)
    if db_integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")

    if db_integration.owner != current_user:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if db_integration.kind == schemas.IntegrationServicesEnum.slack:
        tasks.slack_revoke_token.delay(db_integration.slack_bot_token)

    return crud.integration.remove(db, id=integration_id)


@router.post("/integrations/telegram/{token}")
async def telegram_webhook(
    token: str,
    msg: schemas.TelegramWebhook,
    db: Session = Depends(deps.get_db),
):

    # validate token and start command
    if token != config.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    if not msg.message.text.startswith('/start '):
        # returning 200 to avoid webhook request to be resended
        raise HTTPException(status_code=200, detail="Not implemented")

    # obtain integration
    random_string = msg.message.text[7:]
    db_integration = crud.integration.get_by_telegram_random_string(
        db, telegram_random_string=random_string
    )

    if db_integration is None:
        # returning 200 to avoid webhook request to be resended
        raise HTTPException(status_code=200, detail="Integration not found")

    # update integration
    updated_integration = crud.user.update(db, db_obj=db_integration, obj_in={
        'telegram_random_string': None,
        'telegram_chat_id': msg.message.chat.id,
        'telegram_chat_name': msg.message.chat.first_name,
    })

    # notify user the integration is active
    text = f"Congratulations {updated_integration.telegram_chat_name}, your telegram integration with MonitStatus is now active!"
    tasks.send_telegram_message.delay(text, updated_integration.telegram_chat_id)

    return {}
