import logging
from typing import List, Dict, Any, Callable
from datetime import datetime, date, timezone, timedelta

def normalize_to_datetime(value) -> datetime:
    """Convert date or datetime (possibly naive) to aware datetime in UTC."""
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.replace(tzinfo=None)
        return value
    elif isinstance(value, date):
        # interpret date-only as midnight UTC
        return datetime(value.year, value.month, value.day, tzinfo=None)
    raise TypeError(f"Unsupported temporal type: {type(value)}")
