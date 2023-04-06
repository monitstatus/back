import random
import string
from abc import ABC, abstractmethod

import humanize
import requests
from slack_sdk.webhook import WebhookClient

from app.core import config
from app.models.monitor import Incident
from app.models.integration import Integration
from app.schemas import IntegrationServicesEnum


class BaseIntegration(ABC):
    def __init__(
        self,
        integration: Integration,
        incident: Incident
    ):
        self.integration = integration
        self.incident = incident

    @abstractmethod
    def send(self):
        pass


class TelegramIntegration(BaseIntegration):
    def send(self):
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.get(url, params={'text': self.message, 'chat_id': self.integration.telegram_chat_id})
        print(response)

    @property
    def message(self):
        is_resolved = self.incident.ended_at != None
        if is_resolved:
            incident_humanized_length = humanize.naturaldelta(self.incident.ended_at - self.incident.started_at)
            return f"Monitor is UP: {self.incident.monitor.name}. It has been down for {incident_humanized_length}."
        return f"Monitor is DOWN: {self.incident.monitor.name}."


class SlackIntegration(BaseIntegration):
    def send(self):
        webhook = WebhookClient(
            self.integration.slack_incoming_webhook,
        )
        webhook.send(
            text="fallback",
            blocks=self.build_blocks_data(),
        )

    def build_blocks_data(self):
        return [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"*Monitor {self.incident.monitor.name} is {'UP' if self.is_resolved else 'DOWN'}*"
			}
		},
		{
			"type": "section",
			"fields": self.message_fields()
		},
		{
			"type": "actions",
			"elements": self.action_buttons()
		}
	]

    def message_fields(self):
        datetime_format = "%d %b %Y at %H:%M %Z"

        fields = [
			{
				"type": "mrkdwn",
				"text": f"*Monitor endpoint:*\n{self.incident.monitor.endpoint}"
			},
			{
				"type": "mrkdwn",
				"text": f"*Cause:*\n{self.incident.cause}"
			},
			{
				"type": "mrkdwn",
				"text": f"*Started At:*\n{self.incident.started_at.strftime(datetime_format)}"
			}
		]

        if self.is_resolved:
            fields.extend([
                {
                    "type": "mrkdwn",
                    "text": f"*Ended At:*\n{self.incident.ended_at.strftime(datetime_format)}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Length:*\n{humanize.naturaldelta(self.incident.ended_at - self.incident.started_at)}"
                }
            ])

        return fields

    def action_buttons(self):
        buttons = [] if self.is_resolved else [{
			"type": "button",
			"text": {
				"type": "plain_text",
				"text": "Acknowledge"
			},
			"style": "primary",
			"url": self.ack_url
		}]
        buttons.append({
			"type": "button",
			"text": {
				"type": "plain_text",
				"text": "View"
			},
			"url": self.incident_url
		})
        return buttons

    @property
    def is_resolved():
        raise NotImplementedError

    @property
    def incident_url(self):
        return f"{config.FRONT_BASE_URL}/incidents/{self.incident.id}"

    @property
    def ack_url(self):
        return f"{self.incident_url}/acknowledge"

    @property
    def is_resolved(self):
        return self.incident.ended_at != None


def notify(integration, incident):
    if integration.kind == IntegrationServicesEnum.slack:
        SlackIntegration(integration, incident).send()
    elif (
        integration.kind == IntegrationServicesEnum.telegram and
        integration.telegram_chat_id is not None
    ):
        TelegramIntegration(integration, incident).send()
    else:
        print(f"Integration {integration.id} of kind {integration.kind} notification still not implemented")


def generate_random_string(length=32):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
