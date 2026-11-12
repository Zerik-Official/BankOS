"""Audit log schema."""

# Standard library
import uuid
from datetime import datetime

# Third-party
from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    """Administrative action stored in the audit log."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: str
    previous_state: dict[str, object] | None
    new_state: dict[str, object] | None
    correlation_id: str
    created_at: datetime
