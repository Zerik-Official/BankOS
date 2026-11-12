"""Conversion of domain values into JSON-serializable structures."""

# Standard library
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


def to_jsonable(value: object) -> object:
    """Recursively convert decimals, UUIDs, enums and dates into JSON values."""
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value
