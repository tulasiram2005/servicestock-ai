"""Bounded provider backoff without sleeping or automatically spending another call."""
from email.utils import parsedate_to_datetime
import math


def retry_delay(header, now, failures):
    """Honor valid Retry-After values, bounded to one hour; otherwise exponential."""
    delay = min(3600, 60 * 2 ** min(max(failures - 1, 0), 6))
    if header:
        try:
            requested = float(header)
        except (TypeError, ValueError):
            try:
                requested = parsedate_to_datetime(header).timestamp() - now
            except (TypeError, ValueError, OverflowError):
                return delay
        if math.isfinite(requested) and requested >= 0:
            delay = max(delay, min(3600, requested))
    return delay
