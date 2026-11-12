"""Idempotency key repository."""

# Standard library
import uuid
from datetime import datetime

# Third-party
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

# Project imports
from app.models.idempotency import IdempotencyRecord


class IdempotencyRepository:
    """Persistence for idempotency keys, always scoped to tenant and user."""

    def __init__(self, session: Session) -> None:
        self.session: Session = session

    def get(self, tenant_id: uuid.UUID, user_id: uuid.UUID, key: str) -> IdempotencyRecord | None:
        """Return the record of that key, tenant and user."""
        statement = select(IdempotencyRecord).where(
            IdempotencyRecord.tenant_id == tenant_id,
            IdempotencyRecord.user_id == user_id,
            IdempotencyRecord.key == key,
        )
        return self.session.scalars(statement).first()

    def delete_expired(self, now: datetime) -> None:
        """Remove records whose retention window has passed."""
        self.session.execute(delete(IdempotencyRecord).where(IdempotencyRecord.expires_at < now))
        self.session.flush()
