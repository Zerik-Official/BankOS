"""User request and response schemas."""

# Standard library
import uuid
from datetime import datetime
from typing import Annotated

# Third-party
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Project imports
from app.models.enums import UserRole

Email = Annotated[
    str,
    StringConstraints(
        min_length=5,
        max_length=255,
        to_lower=True,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]
FullName = Annotated[str, StringConstraints(min_length=2, max_length=160)]


class UserCreateRequest(BaseModel):
    """Payload to register a user inside the current tenant."""

    email: Email
    full_name: FullName
    password: Password
    role: UserRole = UserRole.CLIENT


class UserUpdateRequest(BaseModel):
    """Payload to update the mutable fields of a user."""

    full_name: FullName | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    """A user as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserListResponse(BaseModel):
    """Kept for backwards compatibility of generated clients."""

    items: list[UserRead] = Field(default_factory=list)
