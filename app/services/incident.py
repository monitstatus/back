from sendgrid import SendGridAPIClient

from app import crud
from app import models
from app.core import config
from app.schemas.integration import IntegrationServicesEnum
from app.schemas.incident_event import IncidentEventTypeEnum, IncidentEventCreate
from .email import SendIncidentEmail
from .integrations import notify


def send_incident_alerts(db, incident: models.Incident):
    """ Logic to send mails and/or notify via integrations when an inicident starts or ends """
    if incident.monitor.send_email:
        sendgrid_client = SendGridAPIClient(config.SENDGRID_API_KEY)
        mail_sender = SendIncidentEmail(
            email_client=sendgrid_client,
            incident=incident,
        )
        mail_sender.send()
        if not incident.ended_at:
            crud.incident_event.create(db, obj_in=IncidentEventCreate(
                incident_id=incident.id,
                type=IncidentEventTypeEnum.alert_sent,
                field='email',
                extra_field=incident.monitor.owner.email,
            ))

    for integration in crud.integration.get_multi_by_owner(db, owner_id=incident.monitor.owner_id):
        notify(integration, incident)
        if _should_create_incident_event(integration, incident):
            crud.incident_event.create(db, obj_in=IncidentEventCreate(
                incident_id=incident.id,
                type=IncidentEventTypeEnum.alert_sent,
                field=integration.kind,
                extra_field=_get_integration_destination(integration),
            ))


def _should_create_incident_event(integration, incident):
    if incident.ended_at:
        return False

    return (
        (integration.kind == IntegrationServicesEnum.slack) or
        (
            integration.kind == IntegrationServicesEnum.telegram and
            integration.telegram_chat_id is not None
        )
    )


def _get_integration_destination(integration: models.Integration):
    if integration.kind == IntegrationServicesEnum.telegram:
        return integration.telegram_chat_name

    return integration.slack_channel
