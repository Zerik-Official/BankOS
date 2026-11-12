"""Append-only audit service."""

# Standard library
import uuid
from typing import Any, cast

# Third-party
from sqlalchemy.orm import Session

# Project imports
from app.core.correlation import get_correlation_id
from app.core.serialization import to_jsonable
from app.models.audit import AuditLog
from app.repositories.audit import AuditRepository


class AuditService:
    """Write administrative actions to the immutable log."""

    def __init__(self, session: Session, tenant_id: uuid.UUID) -> None:
        self.session: Session = session
        self.repository: AuditRepository = AuditRepository(session, tenant_id)
        self.tenant_id: uuid.UUID = tenant_id

    def record(
        self,
        *,
        actor_user_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: str,
        previous_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Append one entry with its previous and new state."""
        entry = AuditLog(
            tenant_id=self.tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            previous_state=(
                cast(dict[str, Any], to_jsonable(previous_state))
                if previous_state is not None
                else None
            ),
            new_state=(
                cast(dict[str, Any], to_jsonable(new_state)) if new_state is not None else None
            ),
            correlation_id=get_correlation_id(),
        )
        return self.repository.append(entry)
