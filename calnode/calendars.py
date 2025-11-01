import logging
import os
from typing import Callable, List, Any, Dict
from caldav import rrulestr, timedelta, timezone
from caldav.davclient import get_davclient
from dotenv import load_dotenv
from calnode.utils import normalize_to_datetime
import requests
from icalendar import Calendar as ICalendar
from datetime import datetime
from cachetools import TTLCache, cached

load_dotenv()

CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "300"))

cache = TTLCache(maxsize=100, ttl=CACHE_TTL)
logger = logging.getLogger(__name__)

class Calendar:
    """Interface for calendar services with caching.
    """ 

    def get_events_next_days(self, days: int) -> List[Dict[str, Any]]:
        """Return events starting within the next ``days`` days from the .ics file.

        Parameters
        ----------
        days : int
            Number of days from now to look ahead.  Events with start
            times before the current moment or after ``now + days`` will
            be excluded.
        """

        now = normalize_to_datetime(datetime.now(timezone.utc))
        end = normalize_to_datetime(now + timedelta(days=days))
        results = []

        cal_ics_text = self.get()
        cal = ICalendar.from_ical(cal_ics_text)
        for component in cal.walk("VEVENT"):
            dtstart = normalize_to_datetime(component.decoded("DTSTART"))
            dtend = normalize_to_datetime(component.decoded("DTEND", None))
            summary = str(component.get("SUMMARY", ""))
            uid = str(component.get("UID", ""))
            location = str(component.get("LOCATION", ""))
            description = str(component.get("DESCRIPTION", ""))

            # Handle recurring events
            if component.get("RRULE"):
                rule_text = component.get("RRULE").to_ical().decode()
                rule = rrulestr(rule_text, dtstart=dtstart, ignoretz=True)

                # Expand only within desired range
                for occ_start in rule.between(now, end, inc=True):
                    occ_end = occ_start + (dtend - dtstart if dtend else timedelta(hours=1))
                    results.append({
                        "uid": uid,
                        "summary": summary,
                        "start": occ_start.isoformat(),
                        "end": occ_end.isoformat(),
                        "recurring": True,
                        "location": location,
                        "description": description,
                    })
            else:
                # Non-recurring event
                if dtstart >= now and dtstart <= end:
                    results.append({
                        "uid": uid,
                        "summary": summary,
                        "start": dtstart.isoformat(),
                        "end": dtend.isoformat() if dtend else None,
                        "recurring": False,
                        "location": location,
                        "description": description,
                    })
        return results


class Calendars:
    """Manages multiple calendar services."""
    
    def __init__(self, services: List["Calendar"]):
        self.services = services

    def _gather_from_all(
        self,
        func_name: str,
        *args,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Call a function on all services and merge their results."""
        all_events = []
        for service in self.services:
            func: Callable = getattr(service, func_name, None)
            if not callable(func):
                logging.warning(f"{service.__class__.__name__} has no method '{func_name}'")
                continue
            try:
                events = func(*args, **kwargs)
                all_events.extend(events)
            except Exception as e:
                logging.error(f"Failed to call {func_name} on {service}: {e}")
        all_events.sort(key=lambda x: x.get("start", ""))
        return all_events

    def get_events_next_days(self, days: int) -> List[Dict[str, Any]]:
        return self._gather_from_all("get_events_next_days", days)

    def get_events_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        return self._gather_from_all("get_events_keyword", keyword)


class CalDAVCalendar(Calendar):
    """High - level helper for accessing a Nextcloud CalDAV calendar.
    """
    # username="think3", password="cPy4m-fKqG8-i8jH8-ancXS-JqspC", url="https://nx56478.your-storageshare.de/remote.php/dav/"
    def __init__(
            self,
            username: str = None,
            password: str = None,
            url: str = None,
        ):
        self.client = get_davclient(
            username=username,
            password=password,
            url=url
        )
        self.calendar = self.client.principal().calendar()
        logging.debug(f"Initialized DAVClient, calendars: {self.calendar}")

    @cached(cache)
    def get(self) -> str:
        """Download the ICS file from the CalDAV calendar.
        """
        logging.debug(f"CalRequest: Fetching .ics file from CalDAV calendar at {self.calendar.url}")
        master_cal = ICalendar()
        master_cal.add("prodid", "-//MyCache//")
        master_cal.add("version", "2.0")

        for event in self.calendar.events():
            cal = ICalendar.from_ical(event.data)
            for component in cal.walk("vevent"):
                master_cal.add_component(component)

        return master_cal.to_ical().decode("utf-8")

class IcalCalendar(Calendar):
    """High-level helper for accessing iCalendar urls using python icalendar.
    """
    def __init__(self, url: str):
        self.url = url

    @cached(cache)
    def get(self) -> str:
        """Download the ICS file from the provided URL.
        """
        logging.debug(f"CalRequest: Fetching .ics file from {self.url}")
        response = requests.get(self.url)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to retrieve .ics file: {self.url}")
        return response.text
