"""Idempotency key handling for mutable financial operations."""

# Standard library
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

# Project imports
from app.core.clock import utc_now
from app.core.errors import BusinessValidationError, IdempotencyConflictError

IDEMPOTENCY_TTL_HOURS = 24


def idempotency_expiry() -> datetime:
    """Return the expiration time of a new idempotency key."""
    return utc_now() + timedelta(hours=IDEMPOTENCY_TTL_HOURS)


def validate_idempotency_key(raw_key: str | None) -> str:
    """Validate the required Idempotency-Key header as a UUID."""
    if raw_key is None or not raw_key.strip():
        raise BusinessValidationError(
            "The Idempotency-Key header is required",
            code="MISSING_IDEMPOTENCY_KEY",
            details={"header": "Idempotency-Key"},
        )
    try:
        parsed = uuid.UUID(raw_key.strip())
    except ValueError as exc:
        raise BusinessValidationError(
            "The Idempotency-Key header must be a UUID",
            code="INVALID_IDEMPOTENCY_KEY",
            details={"header": "Idempotency-Key"},
        ) from exc
    return str(parsed)


class IdempotencyLockRegistry:
    """Serialize concurrent requests that share an idempotency key."""

    def __init__(self) -> None:
        self._guard: threading.Lock = threading.Lock()
        self._locks: dict[tuple[str, str, str], threading.Lock] = {}

    @contextmanager
    def acquire(self, tenant_id: uuid.UUID, user_id: uuid.UUID, key: str) -> Iterator[None]:
        """Hold the key while the operation runs, rejecting a concurrent one."""
        lock_key = (str(tenant_id), str(user_id), key)
        with self._guard:
            lock = self._locks.setdefault(lock_key, threading.Lock())
        if not lock.acquire(blocking=False):
            raise IdempotencyConflictError(
                "A transaction with this Idempotency-Key is already in progress"
            )
        try:
            yield
        finally:
            lock.release()


@dataclass(frozen=True)
class WebhookNotification:
    """Payload queued for asynchronous delivery to a tenant webhook."""

    url: str
    payload: dict[str, Any]
    correlation_id: str = field(default="")


@dataclass
class IdempotentOutcome:
    """Response to replay for a request that carries an idempotency key."""

    body: dict[str, Any]
    status_code: int
    replayed: bool = False
    notification: WebhookNotification | None = None
