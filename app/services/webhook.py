"""Asynchronous webhook delivery."""

# Standard library
import time

# Third-party
import httpx

# Project imports
from app.core.config import get_settings
from app.core.idempotency import WebhookNotification
from app.core.logging import get_logger

logger = get_logger(__name__)

_MAX_ATTEMPTS = 3


def deliver_webhook(notification: WebhookNotification) -> None:
    """POST a notification to the tenant endpoint with retries and correlation id."""
    timeout_seconds = get_settings().webhook_timeout_seconds
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": notification.correlation_id,
    }
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = httpx.post(
                notification.url,
                json=notification.payload,
                headers=headers,
                timeout=timeout_seconds,
            )
            response.raise_for_status()
            logger.info(
                "Webhook delivered",
                extra={"url": notification.url, "attempt": attempt},
            )
            return
        except httpx.HTTPError as exc:
            logger.warning(
                "Webhook delivery failed",
                extra={"url": notification.url, "attempt": attempt, "error": str(exc)},
            )
            if attempt < _MAX_ATTEMPTS:
                time.sleep(0.5 * attempt)
    logger.error("Webhook discarded after retries", extra={"url": notification.url})
