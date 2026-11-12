"""Authentication service."""

# Standard library
import uuid

# Third-party
from sqlalchemy.orm import Session

# Project imports
from app.core.errors import AuthenticationError
from app.core.principal import Principal
from app.core.security import TokenPayload, create_access_token, verify_password
from app.models.enums import UserRole
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead


class AuthService:
    """Authenticate users inside their tenant and issue session tokens."""

    def __init__(self, session: Session) -> None:
        self.session: Session = session

    def login(self, payload: LoginRequest) -> TokenResponse:
        """Validate tenant, credentials and account state, then sign a token."""
        tenant = TenantRepository(self.session).get_by_slug(payload.tenant_slug)
        if tenant is None or not tenant.is_active:
            raise AuthenticationError("Invalid tenant, email or password")

        user = UserRepository(self.session, tenant.id).get_by_email(payload.email)
        if (
            user is None
            or not user.is_active
            or not verify_password(payload.password, user.password_hash)
        ):
            raise AuthenticationError("Invalid tenant, email or password")

        token, expires_in = create_access_token(
            user_id=user.id,
            tenant_id=tenant.id,
            role=user.role,
            email=user.email,
        )
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user=UserRead.model_validate(user),
        )


def load_principal(session: Session, payload: TokenPayload) -> Principal:
    """Load the active user and tenant behind a valid token."""
    tenant = TenantRepository(session).get(uuid.UUID(payload.tenant_id))
    if tenant is None or not tenant.is_active:
        raise AuthenticationError("The tenant is not active")

    user = UserRepository(session, tenant.id).get(uuid.UUID(payload.sub))
    if user is None or not user.is_active:
        raise AuthenticationError("The user is not active")

    return Principal(
        user_id=user.id,
        tenant_id=tenant.id,
        role=user.role if isinstance(user.role, UserRole) else UserRole(user.role),
        email=user.email,
        full_name=user.full_name,
    )
