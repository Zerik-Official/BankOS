"""Tenant, configuration and exchange rate schemas."""

# Standard library
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

# Third-party
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Project imports
from app.models.enums import CommissionType
from app.schemas.common import Currency, Money, Rate
from app.schemas.user import Email, FullName, Password, UserRead

Slug = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=60,
        to_lower=True,
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$",
    ),
]
WebhookUrl = Annotated[
    str,
    StringConstraints(max_length=500, pattern=r"^https?://[^\s]+$"),
]
CommissionValue = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=6)]


class TenantRegisterRequest(BaseModel):
    """Payload that creates a tenant together with its first administrator."""

    name: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    slug: Slug
    admin_email: Email
    admin_full_name: FullName
    admin_password: Password
    base_currency: Currency = "USD"
    max_transaction_amount: Money = Field(default=Decimal("1000000.00"), gt=0)
    commission_type: CommissionType = CommissionType.PERCENTAGE
    commission_value: CommissionValue = Decimal("0")
    webhook_url: WebhookUrl | None = None


class TenantUpdateRequest(BaseModel):
    """Fields an administrator may change on the current tenant."""

    name: Annotated[str, StringConstraints(min_length=2, max_length=120)] | None = None
    base_currency: Currency | None = None
    max_transaction_amount: Money | None = Field(default=None, gt=0)
    commission_type: CommissionType | None = None
    commission_value: CommissionValue | None = None
    webhook_url: WebhookUrl | None = None
    is_active: bool | None = None


class TenantRead(BaseModel):
    """A tenant and its active configuration."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    base_currency: str
    max_transaction_amount: Money
    commission_type: CommissionType
    commission_value: Rate
    webhook_url: str | None
    is_active: bool
    created_at: datetime


class TenantRegisterResponse(BaseModel):
    """Tenant created by a registration request."""

    tenant: TenantRead
    admin: UserRead


class ExchangeRateItem(BaseModel):
    """One static conversion rate."""

    source_currency: Currency
    target_currency: Currency
    rate: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=6)]


class ExchangeRateBulkRequest(BaseModel):
    """Complete rate table that replaces the current one."""

    rates: list[ExchangeRateItem] = Field(default_factory=list, max_length=100)


class ExchangeRateRead(BaseModel):
    """A stored conversion rate."""

    model_config = ConfigDict(from_attributes=True)

    source_currency: str
    target_currency: str
    rate: Rate
