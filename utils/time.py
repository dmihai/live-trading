import time
from datetime import datetime, timezone


def get_current_time():
    return datetime.now(timezone.utc)


def date_to_rfc3339(date):
    return date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def get_time_elapsed(start_time):
    return round(time.time() - start_time, 2)
