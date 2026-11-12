"""Helpers to translate service outcomes into HTTP responses."""

# Third-party
from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse

# Project imports
from app.core.idempotency import IdempotentOutcome
from app.services.webhook import deliver_webhook


def idempotent_response(
    outcome: IdempotentOutcome, background_tasks: BackgroundTasks
) -> JSONResponse:
    """Return the stored body and schedule the webhook only on first execution."""
    headers: dict[str, str] = {}
    if outcome.replayed:
        headers["X-Idempotent-Replayed"] = "true"
    if outcome.notification is not None:
        background_tasks.add_task(deliver_webhook, outcome.notification)
    return JSONResponse(content=outcome.body, status_code=outcome.status_code, headers=headers)
