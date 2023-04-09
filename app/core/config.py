import os


ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# jwt security
ACCESS_TOKEN_EXPIRE_MINUTES = 60
SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecret')
ALGORITHM = "HS256"

# tasks
USER_AGENT = os.environ.get('USER_AGENT', 'Monitstatus')
CELERY_BROKER = 'redis://redis:6379/0'
SCHEDULE_TASK_PERIODICITY_SECONDS = 1.0
WORKER_ID = os.environ.get('WORKER_ID', 'Development - 127.0.0.1')

# db
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'pass')
SQLALCHEMY_DATABASE_URL = f"postgresql://postgres:{POSTGRES_PASSWORD}@db/postgres"

# front
FRONT_BASE_URL = os.environ.get('FRONT_BASE_URL', 'http://localhost:3000')

# emails
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
SENDGRID_MONITOR_UP_EMAIL_TEMPLATE = os.environ.get('SENDGRID_MONITOR_UP_EMAIL_TEMPLATE')
SENDGRID_MONITOR_DOWN_EMAIL_TEMPLATE = os.environ.get('SENDGRID_MONITOR_DOWN_EMAIL_TEMPLATE')
SENDGRID_USER_VERIFICATION_TEMPLATE = os.environ.get('SENDGRID_USER_VERIFICATION_TEMPLATE')
SENDGRID_USER_INVITATION_TEMPLATE = os.environ.get('SENDGRID_USER_INVITATION_TEMPLATE')

ALERT_SENDER_MAIL_ADDRESS = os.environ.get('ALERT_SENDER_MAIL_ADDRESS', 'alerts@monitstatus.com')
EMAIL_VERIFICATION_SENDER_MAIL_ADDRESS = os.environ.get(
    'EMAIL_VERIFICATION_SENDER_MAIL_ADDRESS',
    'info@monitstatus.com'
)

# telegram
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# slack
SLACK_CLIENT_ID = os.environ.get('SLACK_CLIENT_ID')
SLACK_CLIENT_SECRET = os.environ.get('SLACK_CLIENT_SECRET')
