from datetime import datetime, timedelta

import requests
import sentry_sdk
from celery import Celery
from sendgrid import SendGridAPIClient
from sentry_sdk.integrations.celery import CeleryIntegration

from app import crud
from app import schemas
from app.core import config
from app.db.session import SessionLocal
from app.services.email import SendUserEmailVerificationEmail, SendInvitationEmail
from app.services.incident import send_incident_alerts
from app.services.monitoring import check_monitor


celery_app = Celery('celery', broker=config.CELERY_BROKER)

sentry_sdk.init(integrations=[CeleryIntegration()])


@celery_app.task
def schedule_task():
    def should_monitor(db_last_result, monitoring_periodicity_seconds):
        if db_last_result is None:
            return True

        next_monitoring_instant = db_last_result.created_at + timedelta(seconds=monitoring_periodicity_seconds)
        return next_monitoring_instant <= datetime.now()

    db = SessionLocal()

    db_monitors = crud.monitor.get_multi(db)
    for monitor in db_monitors:
        db_last_result = crud.result.get_last_by_monitor(db, monitor.id)
        if should_monitor(db_last_result, monitor.periodicity):
            monitor_task.apply_async(args=[monitor.id])

    db.close()


@celery_app.task
def monitor_task(monitor_id):
    db = SessionLocal()
    print(f"* Monitoring monitor_id={monitor_id}")
    db_monitor = crud.monitor.get(db, monitor_id)

    # TODO has no sense to have both created_at and monitored_at at same moment
    result = schemas.ResultCreate(
        created_at=datetime.now(),
        monitored_at=datetime.now(),
        response_time=None,
        status=None,
        monitor_id=monitor_id,
    )
    db_result = crud.result.create(db, obj_in=result)

    monit_response = check_monitor(db_monitor)

    updated_result = schemas.ResultUpdate(
        created_at=db_result.created_at,
        monitored_at=db_result.monitored_at,
        response_time=monit_response.response_time,
        status=monit_response.status,
        monitor_id=db_result.monitor_id,
    )
    db_result = crud.result.update(db, db_obj=db_result, obj_in=updated_result)

    # search for last open incident
    last_open_incident = crud.incident.get_last_open_by_monitor(db, monitor_id)
    if monit_response.status:
        if last_open_incident:
            # set ended at
            updated_incident = schemas.IncidentUpdate(
                started_at=last_open_incident.started_at,
                ended_at=db_result.monitored_at,
                monitor_id=last_open_incident.monitor_id,
                cause=last_open_incident.cause,
                response=last_open_incident.response,
                request=last_open_incident.request,
            )
            db_incident = crud.incident.update(db, db_obj=last_open_incident, obj_in=updated_incident)
            crud.incident_event.create(db, obj_in=schemas.IncidentEventCreate(
                incident_id=db_incident.id,
                type=schemas.IncidentEventTypeEnum.monitoring_success,
                field=monit_response.status,
                extra_field=config.WORKER_ID,
            ))
            send_incident_alerts(db, db_incident)

    else:
        if not last_open_incident:
            request_repr = f"{db_monitor.http_method if db_monitor.monitor_type == 'http' else db_monitor.monitor_type} {db_monitor.endpoint}"
            if db_monitor.monitor_type in ('tcp', 'udp'):
                request_repr += f":{db_monitor.port}"
            new_incident = schemas.IncidentCreate(
                started_at=db_result.monitored_at,
                ended_at=None,
                monitor_id=db_result.monitor_id,
                cause=monit_response.incident_cause,
                request=request_repr,
                response=monit_response.response_representation,
            )
            db_incident = crud.incident.create(db, obj_in=new_incident)
            crud.incident_event.create(db, obj_in=schemas.IncidentEventCreate(
                incident_id=db_incident.id,
                type=schemas.IncidentEventTypeEnum.monitoring_failure,
                field=monit_response.incident_cause,
                extra_field=config.WORKER_ID,
            ))
            send_incident_alerts(db, db_incident)

    db.close()


@celery_app.task
def slack_revoke_token(slack_token):
    print(slack_token)
    from slack_sdk import WebClient
    client = WebClient(token=slack_token)
    client.auth_revoke()


@celery_app.task
def send_user_verification_mail(email, token):
    sendgrid_client = SendGridAPIClient(config.SENDGRID_API_KEY)
    verification_sender = SendUserEmailVerificationEmail(
        email_client=sendgrid_client,
        email=email,
        token=token,
    )
    verification_sender.send()


@celery_app.task
def send_user_invitation_mail(email, team_name, invitation_hash, invited_by):
    sendgrid_client = SendGridAPIClient(config.SENDGRID_API_KEY)
    invitation_sender = SendInvitationEmail(
        email_client=sendgrid_client,
        email=email,
        invitation_url=f"{config.FRONT_BASE_URL}/user/sign-up?invitation={invitation_hash}",
        invited_by=invited_by,
        team_name=team_name,
    )
    invitation_sender.send()


@celery_app.task
def send_telegram_message(text, chat_id):
    print("In send telegram message task")
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.get(url, timeout=30, params={'text': text, 'chat_id': chat_id})
    print(response)


celery_app.conf.beat_schedule = {
    "schedule-task": {
        "task": "app.tasks.schedule_task",
        "schedule": config.SCHEDULE_TASK_PERIODICITY_SECONDS,
    }
}
