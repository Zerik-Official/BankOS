"""Console logging configured with request correlation identifiers."""

# Standard library
import logging
import sys
from typing import Any

# Project imports
from app.core.config import Settings
from app.core.correlation import get_correlation_id

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(correlation_id)s | %(name)s | %(message)s"


class CorrelationFilter(logging.Filter):
    """Inject the current correlation identifier into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "-"
        return True


def configure_logging(settings: Settings) -> None:
    """Configure the root logger once, writing to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    handler.addFilter(CorrelationFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())

    for name in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging configured",
        extra=_log_extra(environment=settings.environment),
    )


def _log_extra(**values: Any) -> dict[str, Any]:
    return {"environment": values.get("environment", "-")}


def get_logger(name: str) -> logging.Logger:
    """Return a module logger that carries the correlation identifier."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addFilter(CorrelationFilter())
    return logger
