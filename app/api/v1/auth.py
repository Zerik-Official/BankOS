"""Authentication endpoints."""

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Project imports
from app.api.dependencies import enforce_login_rate_limit, get_principal, get_session
from app.core.errors import NotFoundError
from app.core.principal import Principal
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import ApiResponse, success_response
from app.schemas.user import UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="Log in inside a tenant",
    dependencies=[Depends(enforce_login_rate_limit)],
)
def login(
    payload: LoginRequest, session: Session = Depends(get_session)
) -> ApiResponse[TokenResponse]:
    """Validate credentials and return a JWT bound to the tenant and user."""
    token = AuthService(session).login(payload)
    return success_response(token, message="Authenticated", code="LOGIN_SUCCESS")


@router.get(
    "/me",
    response_model=ApiResponse[UserRead],
    summary="Read the authenticated user",
)
def read_me(
    principal: Principal = Depends(get_principal),
    session: Session = Depends(get_session),
) -> ApiResponse[UserRead]:
    """Return the persisted profile of the current session."""
    user = UserRepository(session, principal.tenant_id).get(principal.user_id)
    if user is None:
        raise NotFoundError("User", str(principal.user_id))
    return success_response(UserRead.model_validate(user), code="USER_PROFILE")
