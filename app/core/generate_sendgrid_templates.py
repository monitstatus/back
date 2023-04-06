import json

from sendgrid import SendGridAPIClient

import config


templates = {
    'SENDGRID_USER_INVITATION_TEMPLATE': {
        'name': 'User invitation',
        'version': {
            'name': 'Untitled Version',
            'html_content': """
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  </head>
  <body>
    <div style="font-size: 1.125rem; line-height: 1.75rem;">
      <span style="font-weight: 600">{{ full_name }}</span>
      has invited you to join the
      <span style="font-weight: 600">{{ team_name }}</span>
      team on Monitstatus
    </div>

    <div style="padding-top: 1.5rem;">
      <a href="https://monitstatus.com" style="text-decoration:none">Monitstatus</a> helps your team to monitor the uptime of your webpages and manage incidents.
    </div>

    <div style="padding-top: 1.5rem;">
      <a
          href="{{ invitation_url }}"
          style="background-color:#3b82f6;border-radius:6px;color:#ffffff;display:inline-block;font-family:arial,helvetica,sans-serif;font-size:16px;font-weight:600;letter-spacing:0px;line-height:16px;padding:12px 18px 12px 18px;text-align:center;text-decoration:none\\"
          target="_blank"
      >
          Join monitstatus
      </a>      
    </div>
  </body>
</html>
            """,
            "generate_plain_content": True,
            "subject": "You have been invited to join a team on Monitstatus",
        }
    },
    'SENDGRID_USER_VERIFICATION_TEMPLATE': {
        'name': 'User email verification',
        'version': {
            'name': 'Untitled Version',
            'html_content': """
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  </head>
  <body>
    <div style="font-family:arial,helvetica,sans-serif; font-size: 16px">
      <p style="padding-top: 0.5rem; font-size: 22px; line-height: 35px">
          You are on your way!<br>
          Lets confirm your email address.
      </p>

      <p>By clicking on the following link, you are confirming your email address.</p>

      <div style="padding-top: 1.5rem">
        <a href="{{ ack_url }}" style="background-color:#333333;border:1px solid #333333;border-color:#333333;border-radius:6px;border-width:1px;color:#ffffff;display:inline-block;font-size:16px;font-weight:normal;letter-spacing:0px;line-height:16px;padding:12px 18px 12px 18px;text-align:center;text-decoration:none" target="_blank">Confirm email address</a>
      </div>
    </div>
  </body>
</html>
            """,
            "generate_plain_content": True,
            "subject": "Welcome to Monitstatus! Confirm your email",
        }
    },
    'SENDGRID_MONITOR_DOWN_EMAIL_TEMPLATE': {
        'name': 'Incident started',
        'version': {
            'name': 'Untitled Version',
            'html_content': """
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  </head>
  <body>
    <div style="font-family:arial,helvetica,sans-serif; font-size: 16px">
      <div style="padding:0px 0px 10px 0px; background-color:#ec2525"></div>
      <p style="padding-top: 0.5rem;">
        <strong>New incident started</strong>
      </p>

      <p>
        Hello {{ full_name }},<br>
        A new incident started on {{ monitor_name }}, we will notify you when it is back up.
      </p>

      <div style="padding-top: 1.5rem">
        <a href="{{ ack_url }}" style="background-color:#333333;border:1px solid #333333;border-color:#333333;border-radius:6px;border-width:1px;color:#ffffff;display:inline-block;font-size:16px;font-weight:normal;letter-spacing:0px;line-height:16px;padding:12px 18px 12px 18px;text-align:center;text-decoration:none" target="_blank">Acknowledge</a>
        <a href="{{ incident_url }}" style="background-color:#ffffff;border:1px solid #333333;border-color:#333333;border-radius:6px;border-width:1px;color:#333333;display:inline-block;font-size:16px;font-weight:normal;letter-spacing:0px;line-height:16px;padding:12px 18px 12px 18px;text-align:center;text-decoration:none" target="_blank">View incident</a>
      </div>
        
      <div style="padding-top: 2.5rem;">
        <div style="background-color:#e2e8f0; padding:18px 18px 18px 18px; line-height:22px;">
          Endpoint:&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{{ monitor_url }}<br>
          Cause:&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;{{ incident_cause }}<br><br>
          Started at:&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;&nbsp;{{ incident_started_at }}
        </div>
      </div>
    </div>
  </body>
</html>
            """,
            "generate_plain_content": True,
            "subject": "Monitor is down - {{ monitor_name }}",
        }
    },
    'SENDGRID_MONITOR_UP_EMAIL_TEMPLATE': {
        'name': 'Incident ended',
        'version': {
            'name': 'Untitled Version',
            'html_content': """
<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  </head>
  <body>
    <div style="font-family:arial,helvetica,sans-serif; font-size: 16px">
      <div style="padding:0px 0px 10px 0px; background-color:#16a30e"></div>
      <p style="padding-top: 0.5rem;">
        <strong>Incident resolved</strong>
      </p>

      <p>
        Hello {{ full_name }},<br>
        Monitor {{ monitor_name }} is back up.
      </p>

      <div style="padding-top: 1.5rem">
        <a href="{{ incident_url }}" style="background-color:#ffffff;border:1px solid #333333;border-color:#333333;border-radius:6px;border-width:1px;color:#333333;display:inline-block;font-size:16px;font-weight:normal;letter-spacing:0px;line-height:16px;padding:12px 18px 12px 18px;text-align:center;text-decoration:none" target="_blank">View incident</a>
      </div>
        
      <div style="padding-top: 2.5rem;">
        <div style="background-color:#e2e8f0; padding:18px 18px 18px 18px; line-height:22px;">
          Endpoint:&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{{ monitor_url }}<br>
          Cause:&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;{{ incident_cause }}<br><br>
          Started at:&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;&nbsp;{{ incident_started_at }}
          Ended at:&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;{{ incident_ended_at }}
          Length:&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;{{ incident_length }}
        </div>
      </div>
    </div>
  </body>
</html>
            """,
            "generate_plain_content": True,
            "subject": "Monitor is up - {{ monitor_name }}",
        }
    },
}


def list_templates(sg: SendGridAPIClient):
    params = {'generations': 'dynamic', 'page_size': 10}

    response = sg.client.templates.get(
        query_params=params
    )


def get_version(sg: SendGridAPIClient, template_id: str, version_id: str):
    response = sg.client.templates._(template_id).versions._(version_id).get()


def get_versions(sg: SendGridAPIClient, template_id: str):
    response = sg.client.templates._(template_id).versions.get()


def create_version(sg: SendGridAPIClient, template_id: str, data: dict):
    response = sg.client.templates._(template_id).versions.post(
        request_body=data
    )


def create_template(sg: SendGridAPIClient, name: str):
    data = {
        "name": name,
        "generation": "dynamic"
    }

    response = sg.client.templates.post(
        request_body=data
    )

    # print(response.status_code)
    # print(response.body)
    # print(response.headers)

    template = json.loads(response.body.decode('utf-8'))
    return template['id']


if __name__ == '__main__': 
    sg = SendGridAPIClient(config.SENDGRID_API_KEY)

    for template, content in templates.items():
        template_id = create_template(sg, name=content['name'])
        create_version(sg, template_id=template_id, data=content['version'])
        print(f"{template}='{template_id}'")
