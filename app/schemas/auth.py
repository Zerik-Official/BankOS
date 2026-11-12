"""Authentication schemas."""

# Standard library
from typing import Annotated

# Third-party
from pydantic import BaseModel, Field, StringConstraints

# Project imports
from app.schemas.user import Email, UserRead

TenantSlug = Annotated[str, StringConstraints(min_length=2, max_length=60)]


class LoginRequest(BaseModel):
    """Credentials of a user that belongs to one tenant."""

    tenant_slug: TenantSlug
    email: Email
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """Session token and the identity it represents."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
