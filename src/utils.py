"""
Utility helpers used by the other modules.
"""
from datetime import timedelta
import time

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def ms_to_hhmmss(ms):
    """Convert milliseconds to H:MM:SS string or return None if ms is None."""
    if ms is None:
        return None
    s = int(ms / 1000)
    return str(timedelta(seconds=s))


def now_iso_utc():
    """Return current UTC time in ISO format used by exports."""
    return time.strftime(ISO_FMT, time.gmtime())
