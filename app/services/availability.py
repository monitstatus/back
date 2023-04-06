import datetime
import pytz

from app.models.monitor import Result


def ceil_dt(dt, delta):
    # Preserve original timezone info
    original_tz = dt.tzinfo
    if original_tz:
        # If the original was timezone aware, translate to UTC.
        # This is necessary because datetime math does not take
        # DST into account, so first we normalize the datetime...
        dt = dt.astimezone(pytz.UTC)
        # ... and then make it timezone naive
        dt = dt.replace(tzinfo=None)
    dt = dt + (datetime.datetime.min - dt) % delta
    if original_tz:
        # If the original was tz aware, we make the result aware...
        dt = pytz.UTC.localize(dt)
        # ... then translate it from UTC back its original tz.
        # This translation applies appropriate DST status.
        dt = dt.astimezone(original_tz)
    return dt


def calculate_status_intervals(
    results: list[Result],
    start_date: datetime.datetime,
    interval: datetime.timedelta,
):
    start_date = ceil_dt(start_date, interval)
    num_intervals = int(
        (ceil_dt(datetime.datetime.now().astimezone(start_date.tzinfo), interval) - start_date) / interval
    )

    up_by_intervals = {}
    results_by_intervals = {}
    num_results_ok = 0

    for r in results:
        if r.status is None:
            # results of monitoring tasks still running should not be considered
            continue

        bucket = int(
            (r.monitored_at.astimezone(start_date.tzinfo) - start_date) / interval
        )
        if bucket in results_by_intervals:
            results_by_intervals[bucket] = results_by_intervals[bucket] + 1
        else:
            results_by_intervals[bucket] = 1

        if r.status is True:
            num_results_ok = num_results_ok + 1
            if bucket in up_by_intervals:
                up_by_intervals[bucket] = up_by_intervals[bucket] + 1
            else:
                up_by_intervals[bucket] = 1

    starting_intervals = []
    status_by_intervals = []
    for n in range(num_intervals):
        starting_intervals.append(start_date + interval*n)
        if n in results_by_intervals:
            status_by_intervals.append(up_by_intervals.get(n, 0.0) / results_by_intervals[n])
        else:
            status_by_intervals.append(-1)

    # TODO availability assumes the interval do not changes
    return {
        'availability': num_results_ok / len(results) if results else 0.0,
        'uptimes': status_by_intervals,
        'starting_intervals': starting_intervals,
    }