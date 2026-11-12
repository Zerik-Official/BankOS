"""Pydantic models shared by every endpoint."""

# Standard library
from decimal import Decimal
from typing import Annotated, Any, Generic, TypeVar

# Third-party
from pydantic import BaseModel, Field, PlainSerializer, StringConstraints

# Project imports
from app.core.correlation import get_correlation_id

T = TypeVar("T")

Currency = Annotated[
    str,
    StringConstraints(min_length=3, max_length=3, to_upper=True, pattern=r"^[A-Za-z]{3}$"),
]
Money = Annotated[
    Decimal,
    PlainSerializer(lambda value: f"{value:.2f}", return_type=str, when_used="json"),
]
PositiveMoney = Annotated[
    Money,
    Field(gt=0, max_digits=18, decimal_places=2),
]
Rate = Annotated[
    Decimal,
    PlainSerializer(lambda value: f"{value:.6f}", return_type=str, when_used="json"),
]


class ApiResponse(BaseModel, Generic[T]):
    """Standard envelope returned by every successful endpoint."""

    success: bool = True
    code: str = "OK"
    message: str = "OK"
    data: T | None = None
    correlation_id: str = Field(default_factory=get_correlation_id)


class ErrorResponse(BaseModel):
    """Standard envelope returned by every failed request."""

    success: bool = False
    code: str
    message: str
    details: Any | None = None
    correlation_id: str


class Page(BaseModel, Generic[T]):
    """Paginated collection embedded in an API response."""

    items: list[T]
    total: int
    limit: int
    offset: int


def success_response(data: T, *, message: str = "OK", code: str = "OK") -> ApiResponse[T]:
    """Build a successful envelope for the given payload."""
    return ApiResponse[T](success=True, code=code, message=message, data=data)


def error_response(
    *,
    code: str,
    message: str,
    details: Any = None,
    correlation_id: str | None = None,
) -> ErrorResponse:
    """Build an error envelope."""
    return ErrorResponse(
        code=code,
        message=message,
        details=details,
        correlation_id=correlation_id or get_correlation_id(),
    )
