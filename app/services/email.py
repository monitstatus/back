from typing import Dict

import humanize
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.core import config
from app.models.monitor import Incident


class SendEmailTemplate:
    def __init__(
        self,
        client : SendGridAPIClient,
        template_id : str,
        from_email : str,
        to_emails : str,
        template_data : Dict
    ):
        self.client = client
        self.template_id = template_id
        self.from_email = from_email
        self.to_emails = to_emails
        self.template_data = template_data

    def send(self):
        message = Mail(
            from_email=self.from_email,
            to_emails=self.to_emails,
            html_content='html content')
        message.dynamic_template_data = self.template_data
        message.template_id = self.template_id

        print(message)
        response = self.client.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)


class SendIncidentEmail:
    def __init__(
        self,
        email_client : SendGridAPIClient,
        incident : Incident,
    ):
        self.email_client = email_client
        self.sender_address = config.ALERT_SENDER_MAIL_ADDRESS
        self.incident = incident
        self.template_id = config.SENDGRID_MONITOR_UP_EMAIL_TEMPLATE if incident.ended_at else config.SENDGRID_MONITOR_DOWN_EMAIL_TEMPLATE

    def incident_url(self):
        return f"{config.FRONT_BASE_URL}/incidents/{self.incident.id}"

    def ack_incident_url(self):
        return f"{self.incident_url()}/acknowledge"

    def build_template_data(self):
        datetime_format = "%d %b %Y at %H:%M %Z"
        return {
            'monitor_name': self.incident.monitor.name,
            'full_name': self.incident.monitor.owner.full_name,
            'monitor_url': self.incident.monitor.endpoint,
            'incident_url': self.incident_url(),
            'ack_url': self.ack_incident_url(),
            'incident_cause': self.incident.cause,
            'incident_started_at': self.incident.started_at.strftime(datetime_format),
            'incident_ended_at': None if not self.incident.ended_at else self.incident.ended_at.strftime(datetime_format),
            'incident_length': None if not self.incident.ended_at else humanize.naturaldelta(self.incident.ended_at - self.incident.started_at)
        }

    def send(self):
        sender_instance = SendEmailTemplate(
            client=self.email_client,
            template_id=self.template_id,
            from_email=self.sender_address,
            to_emails=self.incident.monitor.owner.email,
            template_data=self.build_template_data()
        )
        sender_instance.send()


class SendUserEmailVerificationEmail:
    def __init__(
        self,
        email_client: SendGridAPIClient,
        email: str,
        token: str,
    ):
        self.template_id = config.SENDGRID_USER_VERIFICATION_TEMPLATE
        self.email_client = email_client
        self.email = email
        self.token = token

    def build_template_data(self):
        return {
            'activation_url': f"{config.FRONT_BASE_URL}/user/verification?token={self.token}",
        }

    def send(self):
        sender_instance = SendEmailTemplate(
            client=self.email_client,
            template_id=self.template_id,
            from_email=config.EMAIL_VERIFICATION_SENDER_MAIL_ADDRESS,
            to_emails=self.email,
            template_data=self.build_template_data()
        )
        sender_instance.send()


class SendInvitationEmail(SendUserEmailVerificationEmail):
    def __init__(
        self,
        email_client: SendGridAPIClient,
        email: str,
        invitation_url: str,
        invited_by: str,
        team_name: str,
    ):
        self.template_id = config.SENDGRID_USER_INVITATION_TEMPLATE
        self.email_client = email_client
        self.email = email
        self.invitation_url = invitation_url
        self.invited_by = invited_by
        self.team_name = team_name

    def build_template_data(self):
        return {
            'full_name': self.invited_by,
            'team_name': self.team_name,
            'invitation_url': self.invitation_url
        }
