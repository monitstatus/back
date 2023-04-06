import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import config
from app.routers import (
    incidents, integrations, monitors, schedules, statuspages, users
)


app = FastAPI()
app.include_router(incidents.router)
app.include_router(integrations.router)
app.include_router(monitors.router)
app.include_router(schedules.router)
app.include_router(statuspages.router)
app.include_router(users.router)

if config.ENVIRONMENT == 'production':
    sentry_sdk.init()

origins = [
    "http://localhost:3000",
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
