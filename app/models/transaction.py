"""Financial transaction model."""

# Standard library
import uuid
from datetime import datetime
from decimal import Decimal

# Third-party
from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

# Project imports
from app.core.clock import utc_now
from app.db.types import Money, Rate
from app.models.base import Base
from app.models.enums import TransactionStatus, TransactionType, enum_values


class Transaction(Base):
    """Immutable record of one financial operation."""

    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_tenant_created", "tenant_id", "created_at"),
        Index("ix_transactions_tenant_type", "tenant_id", "transaction_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, native_enum=False, length=20, values_callable=enum_values),
        nullable=False,
    )
    status: Mapped[TransactionStatus] = mapped_column(
        SAEnum(TransactionStatus, native_enum=False, length=20, values_callable=enum_values),
        nullable=False,
    )
    source_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    target_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT"), index=True, nullable=True
    )
    source_account_number: Mapped[str | None] = mapped_column(String(24), nullable=True)
    target_account_number: Mapped[str | None] = mapped_column(String(24), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Money, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    converted_amount: Mapped[Decimal] = mapped_column(
        Money, nullable=False, default=Decimal("0.00")
    )
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(
        Rate, nullable=False, default=Decimal("1.000000")
    )
    fee: Mapped[Decimal] = mapped_column(Money, nullable=False, default=Decimal("0.00"))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    error_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
