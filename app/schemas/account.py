"""Account schemas."""

# Standard library
import uuid
from datetime import datetime

# Third-party
from pydantic import BaseModel, ConfigDict

# Project imports
from app.models.enums import AccountStatus
from app.schemas.common import Currency, Money


class AccountCreateRequest(BaseModel):
    """Payload to open an account for a client of the tenant."""

    owner_id: uuid.UUID
    currency: Currency


class AccountStatusUpdateRequest(BaseModel):
    """Soft delete or reactivation of an account."""

    status: AccountStatus


class AccountRead(BaseModel):
    """A bank account as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_number: str
    owner_id: uuid.UUID
    balance: Money
    currency: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime
