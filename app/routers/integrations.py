from typing import Annotated

from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from slack_sdk.web import WebClient

from app import crud, models, schemas, tasks
from app.api import deps
from app.core import config
from app.services.integrations import generate_random_string


router = APIRouter()
CurrentUser = Annotated[models.User, Depends(deps.get_current_user)]
DBSession = Annotated[Session, Depends(deps.get_db)]


@router.post("/integrations", response_model=schemas.Integration, status_code=status.HTTP_201_CREATED)
async def create_integration(
    integration: schemas.IntegrationCreate,
    db: DBSession,
    current_user: CurrentUser,
):
    if integration.kind == schemas.IntegrationServicesEnum.telegram:
        integration.telegram_random_string = generate_random_string()

    return crud.integration.create_with_owner(db=db, obj_in=integration, owner_id=current_user.id)


@router.get("/integrations", response_model=list[schemas.Integration], status_code=status.HTTP_200_OK)
async def list_integrations(
    db: DBSession,
    current_user: CurrentUser,
):
    return crud.integration.get_multi_by_owner(db, owner_id=current_user.id)


@router.delete("/integrations/{integration_id}", status_code=status.HTTP_200_OK)
async def delete_integration(
    integration_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    db_integration = crud.integration.get(db, id=integration_id)
    if db_integration is None:
        raise HTTPException(status_code=404, detail="Integration not found")

    if db_integration.owner != current_user:
        raise HTTPException(status_code=403, detail="Unauthorized")

    if db_integration.kind == schemas.IntegrationServicesEnum.slack:
        tasks.slack_revoke_token.delay(db_integration.slack_bot_token)

    return crud.integration.remove(db, id=integration_id)


@router.post("/integrations/slackOauthAccess")
async def obtain_slack_oauth_access(
    code: str,
    current_user: CurrentUser,
):
    redirect_uri = f'{config.FRONT_BASE_URL}/integrations/slack'

    client = WebClient()  # no prepared token needed for this
    # Complete the installation by calling oauth.v2.access API method
    oauth_response = client.oauth_v2_access(
        client_id=config.SLACK_CLIENT_ID,
        client_secret=config.SLACK_CLIENT_SECRET,
        redirect_uri=redirect_uri,
        code=code,
    )

    print(oauth_response)
    incoming_webhook = oauth_response.get("incoming_webhook", {})
    installed_team = oauth_response.get("team", {})
    bot_token = oauth_response.get("access_token")

    return {
        'access_token': bot_token,
        'incoming_webhook': {
            'url': incoming_webhook.get('url'),
            'channel': incoming_webhook.get('channel')
        },
        'team': {
            'name': installed_team.get('name')
        }
    }


@router.post("/integrations/telegram/{token}")
async def telegram_webhook(
    token: str,
    msg: schemas.TelegramWebhook,
    db: DBSession,
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
