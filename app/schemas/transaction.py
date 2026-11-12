"""Financial operation and transaction history schemas."""

# Standard library
import uuid
from datetime import datetime
from typing import Annotated

# Third-party
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Project imports
from app.models.enums import TransactionStatus, TransactionType
from app.schemas.common import Currency, Money, PositiveMoney, Rate

AccountNumber = Annotated[str, StringConstraints(min_length=4, max_length=24)]
Description = Annotated[str, StringConstraints(max_length=255)]


class DepositRequest(BaseModel):
    """Payload to credit an account."""

    amount: PositiveMoney
    description: Description | None = None


class WithdrawalRequest(BaseModel):
    """Payload to debit an account."""

    amount: PositiveMoney
    description: Description | None = None


class TransferRequest(BaseModel):
    """Payload to move funds between two accounts of the same tenant."""

    source_account_id: uuid.UUID
    target_account_number: AccountNumber
    amount: PositiveMoney
    description: Description | None = None


class TransferPreviewRequest(BaseModel):
    """Request used to preview the cost of a transfer."""

    source_account_id: uuid.UUID
    target_account_number: AccountNumber
    amount: PositiveMoney


class TransferQuote(BaseModel):
    """Cost breakdown of a transfer before it is confirmed."""

    amount: Money
    fee: Money
    total_debit: Money
    exchange_rate: Rate
    converted_amount: Money
    source_currency: Currency
    target_currency: Currency


class TransactionRead(BaseModel):
    """Detailed record of a financial movement."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    type: TransactionType = Field(alias="transaction_type")
    status: TransactionStatus
    source_account_number: str | None
    target_account_number: str | None
    amount: Money
    currency: str
    converted_amount: Money
    target_currency: str
    exchange_rate: Rate
    fee: Money
    description: str | None
    idempotency_key: str
    error_code: str | None
    created_at: datetime
