import logging
import unittest
from unittest.mock import patch
from datetime import date, datetime, timedelta
from caldav import rrulestr, timedelta, timezone
from icalendar import Calendar as ICalendar, Event

from calnode.calendars import IcalCalendar, CalDAVCalendar

logging.basicConfig(    
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="./data/test_calnode.log",
    filemode="w"
)


logger = logging.getLogger(__name__)


def create_basic_ics():
    cal = ICalendar()
    now = datetime.now(timezone.utc)

    # Event 1: datetime with timezone (aware)
    event1 = Event()
    event1.add("uid", "tz-aware")
    event1.add("summary", "Timezone Aware Event")
    event1.add("dtstart", now + timedelta(days=1))
    event1.add("dtend", now + timedelta(days=1, hours=1))
    cal.add_component(event1)

    # Event 2: datetime without timezone (naive)
    naive_start = datetime.now().replace(microsecond=0)
    event2 = Event()
    event2.add("uid", "tz-naive")
    event2.add("summary", "Naive Datetime Event")
    event2.add("dtstart", naive_start + timedelta(days=1))
    event2.add("dtend", naive_start + timedelta(days=1, hours=1))
    cal.add_component(event2)

    # Event 3: date only (all-day event)
    event3 = Event()
    event3.add("uid", "all-day")
    event3.add("summary", "All-Day Event")
    event3.add("dtstart", date.today() + timedelta(days=1))
    event3.add("dtend", date.today() + timedelta(days=2))
    cal.add_component(event3)

    return cal.to_ical().decode("utf-8")



class TestCalendarBasic(unittest.TestCase):
    @patch("requests.get")
    def test_init_and_query_ical(self, mock_get):
        # Prepare mocked HTTP response
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = create_basic_ics()

        # Initialize calendar
        cal = IcalCalendar(url="https://example.com/test.ics")

        # This should not raise any exceptions
        try:
            events = cal.get_events_next_days(3)
            #raise ValueError("Test exception")
            logger.debug(f"Retrieved events: {events}")
            self.assertEqual(len(events), 3)
        except Exception as e:
            logger.error(f"Exception during get_events_next_days: {e}")
            self.fail(f"Initialization or query raised an exception: {e}")

    def test_init_and_query_caldav(self):
        # Note: This test assumes access to a real CalDAV server.
        # Replace with valid credentials and URL for actual testing.
        cal = CalDAVCalendar(
            username="think3", 
            password="cPy4m-fKqG8-i8jH8-ancXS-JqspC", 
            url="https://nx56478.your-storageshare.de/remote.php/dav/"
        )

        # This should not raise any exceptions
        try:
            events = cal.get_events_next_days(3)
            logger.debug(f"Retrieved events from CalDAV: {events}")
            # We cannot assert exact number of events without knowing the calendar content
        except Exception as e:
            logger.error(f"Exception during get_events_next_days on CalDAV: {e}")
            self.fail(f"Initialization or query raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
