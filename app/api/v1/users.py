"""User management endpoints."""

# Standard library
import uuid

# Third-party
from fastapi import APIRouter, Depends, Query, status

# Project imports
from app.api.dependencies import Pagination, get_admin_principal, get_pagination, get_user_service
from app.core.principal import Principal
from app.models.enums import UserRole
from app.schemas.common import ApiResponse, Page, success_response
from app.schemas.user import UserCreateRequest, UserRead, UserUpdateRequest
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=ApiResponse[UserRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a user in the current tenant",
)
def create_user(
    payload: UserCreateRequest,
    principal: Principal = Depends(get_admin_principal),
    service: UserService = Depends(get_user_service),
) -> ApiResponse[UserRead]:
    """Register a client or another administrator inside the tenant."""
    user = service.create(payload)
    return success_response(user, message="User created", code="USER_CREATED")


@router.get(
    "",
    response_model=ApiResponse[Page[UserRead]],
    summary="List the users of the current tenant",
)
def list_users(
    pagination: Pagination = Depends(get_pagination),
    role: UserRole | None = Query(default=None, description="Filter by role"),
    is_active: bool | None = Query(default=None, description="Filter by account state"),
    principal: Principal = Depends(get_admin_principal),
    service: UserService = Depends(get_user_service),
) -> ApiResponse[Page[UserRead]]:
    """Return a page of users, only visible to administrators."""
    page = service.list_users(
        limit=pagination.limit,
        offset=pagination.offset,
        role=role,
        is_active=is_active,
    )
    return success_response(page, code="USER_LIST")


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserRead],
    summary="Read a user",
)
def read_user(
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service),
) -> ApiResponse[UserRead]:
    """Return one user; clients can only read themselves."""
    return success_response(service.get(user_id), code="USER_PROFILE")


@router.patch(
    "/{user_id}",
    response_model=ApiResponse[UserRead],
    summary="Update a user",
)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateRequest,
    principal: Principal = Depends(get_admin_principal),
    service: UserService = Depends(get_user_service),
) -> ApiResponse[UserRead]:
    """Update the name or activation state of a user."""
    user = service.update(user_id, payload)
    return success_response(user, message="User updated", code="USER_UPDATED")
