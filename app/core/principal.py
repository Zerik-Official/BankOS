"""Authenticated principal shared across services."""

# Standard library
import uuid
from dataclasses import dataclass

# Project imports
from app.core.errors import AuthorizationError
from app.models.enums import UserRole


@dataclass(frozen=True)
class Principal:
    """Identity and scope of the caller of a request."""

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: UserRole
    email: str
    full_name: str

    @property
    def is_admin(self) -> bool:
        """Return whether the caller is a tenant administrator."""
        return self.role is UserRole.ADMINISTRATOR


def ensure_admin(principal: Principal) -> None:
    """Reject the request when the principal is not an administrator."""
    if not principal.is_admin:
        raise AuthorizationError("This action requires the administrator role")
