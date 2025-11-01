import os
import logging
from dotenv import load_dotenv
from typing import List, Any

from calnode.calendars import CalDAVCalendar, IcalCalendar, Calendars

load_dotenv()
logger = logging.getLogger(__name__)


def load_calendars_from_env() -> Calendars:
    """Dynamically load any number of calendars defined in environment variables."""
    calendars: List[Any] = []

    # Find all CALENDAR_X_TYPE entries
    indices = set()
    for key in os.environ:
        if key.startswith("CALENDAR_") and "_TYPE" in key:
            indices.add(key.split("_")[1])

    for idx in sorted(indices):
        prefix = f"CALENDAR_{idx}_"
        cal_type = os.getenv(prefix + "TYPE", "").lower()
        url = os.getenv(prefix + "URL")

        if cal_type == "caldav":
            username = os.getenv(prefix + "USERNAME")
            password = os.getenv(prefix + "PASSWORD")
            if not (url and username and password):
                logger.warning(f"Skipping {prefix} — missing fields")
                continue
            calendars.append(CalDAVCalendar(username=username, password=password, url=url))

        elif cal_type == "ical":
            if not url:
                logger.warning(f"Skipping {prefix} — missing URL for iCal")
                continue
            calendars.append(IcalCalendar(url=url))

        else:
            logger.warning(f"Unknown calendar type for {prefix}: {cal_type!r}")

    if not calendars:
        logger.error("No valid calendars configured in environment.")
        raise RuntimeError("No valid calendars configured")

    return Calendars(calendars)
