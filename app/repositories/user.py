"""User repository."""

# Standard library
import uuid

# Third-party
from sqlalchemy import func, select
from sqlalchemy.orm import Session

# Project imports
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.base import TenantScopedRepository


class UserRepository(TenantScopedRepository[User]):
    """Persistence for the users of one tenant."""

    def __init__(self, session: Session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, User, tenant_id)

    def get_by_email(self, email: str) -> User | None:
        """Return the user with that email inside the tenant."""
        statement = select(User).where(
            User.tenant_id == self.tenant_id,
            func.lower(User.email) == email.lower(),
        )
        return self.session.scalars(statement).first()

    def list_users(
        self,
        *,
        limit: int,
        offset: int,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> list[User]:
        """List users with optional filters."""
        statement = select(User).where(User.tenant_id == self.tenant_id)
        if role is not None:
            statement = statement.where(User.role == role)
        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
        statement = statement.order_by(User.created_at.desc()).limit(limit).offset(offset)
        return list(self.session.scalars(statement).all())

    def count_users(self, *, role: UserRole | None = None, is_active: bool | None = None) -> int:
        """Count users with the same filters as the listing."""
        statement = select(func.count()).select_from(User).where(User.tenant_id == self.tenant_id)
        if role is not None:
            statement = statement.where(User.role == role)
        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
        return int(self.session.scalar(statement) or 0)
