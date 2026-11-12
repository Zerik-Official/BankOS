"""Tenant and exchange rate models."""

# Standard library
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

# Third-party
from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Project imports
from app.db.types import Money, Rate
from app.models.base import Base, TimestampMixin
from app.models.enums import CommissionType, enum_values

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.user import User


class Tenant(Base, TimestampMixin):
    """An isolated financial institution running on the platform."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    max_transaction_amount: Mapped[Decimal] = mapped_column(
        Money, nullable=False, default=Decimal("1000000.00")
    )
    commission_type: Mapped[CommissionType] = mapped_column(
        SAEnum(CommissionType, native_enum=False, length=20, values_callable=enum_values),
        nullable=False,
        default=CommissionType.PERCENTAGE,
    )
    commission_value: Mapped[Decimal] = mapped_column(
        Rate, nullable=False, default=Decimal("0.000000")
    )
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    users: Mapped[list[User]] = relationship(back_populates="tenant")
    accounts: Mapped[list[Account]] = relationship(back_populates="tenant")
    exchange_rates: Mapped[list[ExchangeRate]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


class ExchangeRate(Base):
    """Static conversion rate configured by a tenant."""

    __tablename__ = "exchange_rates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "source_currency", "target_currency", name="uq_exchange_rate_pair"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Rate, nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="exchange_rates")
