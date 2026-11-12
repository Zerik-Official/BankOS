"""Shared FastAPI dependencies."""

# Standard library
from dataclasses import dataclass

# Third-party
from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

# Project imports
from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.core.principal import Principal, ensure_admin
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import TokenPayload, decode_access_token
from app.db.session import get_db
from app.services.account import AccountService
from app.services.auth import load_principal
from app.services.tenant import TenantService
from app.services.transaction import TransactionService
from app.services.user import UserService

_settings = get_settings()

bearer_scheme = HTTPBearer(
    auto_error=False, scheme_name="BearerAuth", description="JWT access token"
)

login_limiter = SlidingWindowLimiter(_settings.rate_limit_auth_per_minute)
financial_limiter = SlidingWindowLimiter(_settings.rate_limit_financial_per_minute)
ip_limiter = SlidingWindowLimiter(_settings.rate_limit_ip_per_minute)


@dataclass(frozen=True)
class Pagination:
    """Validated pagination window."""

    limit: int
    offset: int


def get_session(session: Session = Depends(get_db)) -> Session:
    """Return the request-scoped database session."""
    return session


def get_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenPayload:
    """Decode the bearer token of the request."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationError(
            "The Authorization header with a bearer token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def get_principal(
    payload: TokenPayload = Depends(get_token_payload),
    session: Session = Depends(get_session),
) -> Principal:
    """Resolve the authenticated user and tenant of the token."""
    return load_principal(session, payload)


def get_admin_principal(principal: Principal = Depends(get_principal)) -> Principal:
    """Require an administrator caller."""
    ensure_admin(principal)
    return principal


def get_pagination(
    limit: int = Query(default=50, ge=1, le=100, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
) -> Pagination:
    """Parse the pagination query parameters."""
    return Pagination(limit=limit, offset=offset)


def enforce_login_rate_limit(request: Request) -> None:
    """Limit login attempts per client address."""
    client = request.client.host if request.client else "unknown"
    login_limiter.check(client)


def enforce_financial_rate_limit(principal: Principal = Depends(get_principal)) -> None:
    """Limit financial operations per user and tenant."""
    financial_limiter.check(f"{principal.tenant_id}:{principal.user_id}")


def get_tenant_service(session: Session = Depends(get_session)) -> TenantService:
    """Build the tenant service for the request."""
    return TenantService(session)


def get_user_service(
    principal: Principal = Depends(get_principal),
    session: Session = Depends(get_session),
) -> UserService:
    """Build the user service for the request."""
    return UserService(session, principal)


def get_account_service(
    principal: Principal = Depends(get_principal),
    session: Session = Depends(get_session),
) -> AccountService:
    """Build the account service for the request."""
    return AccountService(session, principal)


def get_transaction_service(
    principal: Principal = Depends(get_principal),
    session: Session = Depends(get_session),
) -> TransactionService:
    """Build the financial operations service for the request."""
    return TransactionService(session, principal)
