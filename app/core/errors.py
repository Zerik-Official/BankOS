"""Domain exceptions and their HTTP representation."""

# Standard library
from typing import Any


class BankOSError(Exception):
    """Base exception for every business error of the platform."""

    status_code: int = 400
    code: str = "BANKOS_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.details: Any = details
        self.headers: dict[str, str] = headers or {}
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class AuthenticationError(BankOSError):
    """Raised when credentials or a token are not valid."""

    status_code = 401
    code = "UNAUTHENTICATED"


class AuthorizationError(BankOSError):
    """Raised when an authenticated principal lacks permissions."""

    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(BankOSError):
    """Raised when an entity does not exist inside the current tenant."""

    status_code = 404
    code = "NOT_FOUND"

    def __init__(self, entity: str, identifier: str) -> None:
        super().__init__(f"{entity} not found", details={"entity": entity, "id": identifier})


class ConflictError(BankOSError):
    """Raised when a resource already exists or the state forbids the action."""

    status_code = 409
    code = "CONFLICT"


class BusinessValidationError(BankOSError):
    """Raised when a business rule rejects an otherwise valid request."""

    status_code = 422
    code = "BUSINESS_RULE_VIOLATION"


class RateLimitError(BankOSError):
    """Raised when a caller exceeds the allowed request rate."""

    status_code = 429
    code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(
            "Too many requests, retry later",
            details={"retry_after_seconds": retry_after_seconds},
            headers={"Retry-After": str(retry_after_seconds)},
        )
        self.retry_after_seconds: int = retry_after_seconds


class IdempotencyConflictError(BankOSError):
    """Raised when the same idempotency key is already being processed."""

    status_code = 409
    code = "IDEMPOTENCY_IN_PROGRESS"


class ExternalServiceError(BankOSError):
    """Raised when an upstream dependency fails."""

    status_code = 502
    code = "UPSTREAM_ERROR"
