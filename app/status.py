import datetime

import humanize
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session


from app import crud
from app.api import deps
from app.services.availability import calculate_status_intervals


DAYS_SINCE = 90


app = FastAPI()
app.mount("/static", StaticFiles(directory="app/status/static"), name="static")

templates = Jinja2Templates(directory="app/status/templates")

def color_by_uptime(uptime):
    if uptime < 0:
        return '#94a3b8'

    if uptime == 0:
        return '#dc2626'

    if uptime == 1:
        return '#3bd671'

    if uptime >= 0.5 and uptime < 0.8:
        return '#fb923c'

    if uptime >= 0.25  and uptime < 0.5:
        return '#f97316'

    if uptime > 0 and uptime < 0.25:
        return '#ef4444'

    return '#bef264'

templates.env.filters['colorByUptime'] = color_by_uptime

def humanize_timedelta(timedelta):
    return humanize.naturaldelta(timedelta)

templates.env.filters['humanizeTimedelta'] = humanize_timedelta



@app.get("/{id}", response_class=HTMLResponse)
async def statuspage_detail(
    id: str,
    request: Request,
    db: Session = Depends(deps.get_db),
):
    statuspage = crud.statuspage.get_by_subdomain(db, subdomain=id)
    if statuspage is None:
        return templates.TemplateResponse(
            '404.html',
            {'request': request},
            status_code=404
        )

    start_date = datetime.datetime.today().astimezone(None) - datetime.timedelta(days = DAYS_SINCE)
    monitors_data = []
    for m in statuspage.monitors:
        monitor_results = crud.result.get_multi_by_monitor(db, monitor_id=m.id, since=start_date)
        availability = calculate_status_intervals(monitor_results, start_date, datetime.timedelta(days=1))
        monitors_data.append({
            'name': m.name,
            'up': m.up,
            'uptimes': availability['uptimes'],
            'uptimes_dates': availability['starting_intervals'],
            'uptime': availability['availability'],
        })

    return templates.TemplateResponse("status.html", {
        'up': all([m['up'] for m in monitors_data]),
        'company_name': statuspage.company_name,
        'company_website': statuspage.company_website,
        'days_since': DAYS_SINCE,
        'monitors': monitors_data,
        'incidents': crud.incident.get_multi_by_monitor_list_and_date(
            db,
            monitor_ids=[m.id for m in statuspage.monitors],
            since=start_date,
        ),
        'request': request,
    })
