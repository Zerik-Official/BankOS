"""Bank account model."""

# Standard library
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

# Third-party
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Project imports
from app.db.types import Money
from app.models.base import Base, TimestampMixin
from app.models.enums import AccountStatus, enum_values

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User


class Account(Base, TimestampMixin):
    """A bank account owned by a client of a tenant."""

    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    account_number: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Money, nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[AccountStatus] = mapped_column(
        SAEnum(AccountStatus, native_enum=False, length=20, values_callable=enum_values),
        nullable=False,
        default=AccountStatus.ACTIVE,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="accounts")
    owner: Mapped[User] = relationship(back_populates="accounts")
