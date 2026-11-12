"""Request correlation identifier shared through a context variable."""

# Standard library
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token

_CORRELATION_ID: ContextVar[str] = ContextVar("correlation_id", default="")


def generate_correlation_id() -> str:
    """Generate a new correlation identifier."""
    return str(uuid.uuid4())


def get_correlation_id() -> str:
    """Return the correlation identifier of the current request."""
    return _CORRELATION_ID.get()


@contextmanager
def correlation_context(correlation_id: str) -> Iterator[None]:
    """Bind a correlation identifier to the current execution context."""
    token: Token[str] = _CORRELATION_ID.set(correlation_id)
    try:
        yield
    finally:
        _CORRELATION_ID.reset(token)
