"""Time helpers."""

# Standard library
from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current time in UTC."""
    return datetime.now(UTC)
