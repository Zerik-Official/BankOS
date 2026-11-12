"""Audit log repository."""

# Standard library
import uuid

# Third-party
from sqlalchemy import func, select
from sqlalchemy.orm import Session

# Project imports
from app.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Append-only access to the audit log."""

    def __init__(self, session: Session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, AuditLog)
        self.tenant_id: uuid.UUID = tenant_id

    def append(self, entry: AuditLog) -> AuditLog:
        """Write one audit entry."""
        return self.add(entry)

    def list_entries(self, *, limit: int, offset: int) -> list[AuditLog]:
        """List the audit entries of the tenant, newest first."""
        statement = (
            select(AuditLog)
            .where(AuditLog.tenant_id == self.tenant_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(statement).all())

    def count_entries(self) -> int:
        """Count the audit entries of the tenant."""
        statement = (
            select(func.count()).select_from(AuditLog).where(AuditLog.tenant_id == self.tenant_id)
        )
        return int(self.session.scalar(statement) or 0)
