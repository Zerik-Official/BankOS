"""User management service."""

# Standard library
import uuid

# Third-party
from sqlalchemy.orm import Session

# Project imports
from app.core.errors import (
    AuthorizationError,
    BusinessValidationError,
    ConflictError,
    NotFoundError,
)
from app.core.principal import Principal, ensure_admin
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.common import Page
from app.schemas.user import UserCreateRequest, UserRead, UserUpdateRequest
from app.services.audit import AuditService


class UserService:
    """Create and manage the users of one tenant."""

    def __init__(self, session: Session, principal: Principal) -> None:
        self.session: Session = session
        self.principal: Principal = principal
        self.repository: UserRepository = UserRepository(session, principal.tenant_id)

    def create(self, payload: UserCreateRequest) -> UserRead:
        """Register a new user inside the tenant."""
        ensure_admin(self.principal)
        if self.repository.get_by_email(payload.email) is not None:
            raise ConflictError(
                "A user with that email already exists in the tenant",
                code="USER_EMAIL_TAKEN",
                details={"email": payload.email},
            )

        user = User(
            tenant_id=self.principal.tenant_id,
            email=payload.email,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_active=True,
        )
        self.session.add(user)
        self.session.flush()
        AuditService(self.session, self.principal.tenant_id).record(
            actor_user_id=self.principal.user_id,
            action="user.created",
            entity_type="user",
            entity_id=str(user.id),
            new_state={"email": user.email, "full_name": user.full_name, "role": user.role.value},
        )
        self.session.commit()
        return UserRead.model_validate(user)

    def list_users(
        self,
        *,
        limit: int,
        offset: int,
        role: UserRole | None,
        is_active: bool | None,
    ) -> Page[UserRead]:
        """List the users of the tenant."""
        ensure_admin(self.principal)
        users = self.repository.list_users(
            limit=limit, offset=offset, role=role, is_active=is_active
        )
        total = self.repository.count_users(role=role, is_active=is_active)
        return Page[UserRead](
            items=[UserRead.model_validate(user) for user in users],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get(self, user_id: uuid.UUID) -> UserRead:
        """Return one user, visible to administrators and to the user itself."""
        if not self.principal.is_admin and user_id != self.principal.user_id:
            raise AuthorizationError("You can only read your own user")
        user = self.repository.get(user_id)
        if user is None:
            raise NotFoundError("User", str(user_id))
        return UserRead.model_validate(user)

    def update(self, user_id: uuid.UUID, payload: UserUpdateRequest) -> UserRead:
        """Update a user and audit the resulting state."""
        ensure_admin(self.principal)
        user = self.repository.get(user_id)
        if user is None:
            raise NotFoundError("User", str(user_id))
        if user.id == self.principal.user_id and payload.is_active is False:
            raise BusinessValidationError(
                "An administrator cannot deactivate their own user",
                code="CANNOT_DEACTIVATE_SELF",
            )

        previous = {
            "full_name": user.full_name,
            "is_active": user.is_active,
        }
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.is_active is not None:
            user.is_active = payload.is_active

        AuditService(self.session, self.principal.tenant_id).record(
            actor_user_id=self.principal.user_id,
            action="user.updated",
            entity_type="user",
            entity_id=str(user.id),
            previous_state=previous,
            new_state={"full_name": user.full_name, "is_active": user.is_active},
        )
        self.session.commit()
        return UserRead.model_validate(user)
