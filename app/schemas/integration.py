from enum import Enum

from pydantic import BaseModel


class IntegrationServicesEnum(str, Enum):
    slack = 'slack'
    telegram = 'telegram'


class IntegrationBase(BaseModel):
    kind: IntegrationServicesEnum | None

    slack_channel: str | None
    slack_team_name: str | None

    telegram_random_string: str | None


class IntegrationCreate(IntegrationBase):
    kind: IntegrationServicesEnum
    slack_bot_token: str | None
    slack_incoming_webhook: str | None


class IntegrationUpdate(IntegrationBase):
    slack_bot_token: str | None
    slack_incoming_webhook: str | None
    telegram_chat_id: str | None
    telegram_chat_name: str | None


class Integration(IntegrationBase):
    id: int
    telegram_chat_id: str | None
    telegram_chat_name: str | None

    class Config:
        orm_mode = True


class TelegramChat(BaseModel):
    id: int
    first_name: str


class TelegramMessage(BaseModel):
    chat: TelegramChat
    text: str


class TelegramWebhook(BaseModel):
    update_id: int
    message: TelegramMessage
