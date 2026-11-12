"""Enumerations shared by models and schemas."""

# Standard library
from enum import Enum, StrEnum


class UserRole(StrEnum):
    """System roles available to a tenant."""

    ADMINISTRATOR = "administrator"
    CLIENT = "client"


class AccountStatus(StrEnum):
    """Lifecycle states of a bank account."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class CommissionType(StrEnum):
    """How a tenant charges outgoing transfers."""

    FIXED = "fixed"
    PERCENTAGE = "percentage"


class TransactionType(StrEnum):
    """Kind of financial movement."""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class TransactionStatus(StrEnum):
    """Outcome stored for a financial movement."""

    SUCCESS = "success"
    ERROR = "error"


class IdempotencyStatus(StrEnum):
    """Processing state of an idempotency key."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


def enum_values(enum_class: type[Enum]) -> list[str]:
    """Return the stored values of an enum for SQLAlchemy columns."""
    return [str(member.value) for member in enum_class]
