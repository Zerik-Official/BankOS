"""Transaction history repository."""

# Standard library
import uuid
from datetime import datetime

# Third-party
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

# Project imports
from app.models.account import Account
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories.base import TenantScopedRepository


class TransactionRepository(TenantScopedRepository[Transaction]):
    """Persistence for the financial history of one tenant."""

    def __init__(self, session: Session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, Transaction, tenant_id)

    def _filters(
        self,
        *,
        transaction_type: TransactionType | None,
        status: TransactionStatus | None,
        account_id: uuid.UUID | None,
        owner_id: uuid.UUID | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[object]:
        filters: list[object] = [Transaction.tenant_id == self.tenant_id]
        if transaction_type is not None:
            filters.append(Transaction.transaction_type == transaction_type)
        if status is not None:
            filters.append(Transaction.status == status)
        if account_id is not None:
            filters.append(
                or_(
                    Transaction.source_account_id == account_id,
                    Transaction.target_account_id == account_id,
                )
            )
        if owner_id is not None:
            owned_accounts = select(Account.id).where(
                Account.tenant_id == self.tenant_id, Account.owner_id == owner_id
            )
            filters.append(
                or_(
                    Transaction.source_account_id.in_(owned_accounts),
                    Transaction.target_account_id.in_(owned_accounts),
                )
            )
        if date_from is not None:
            filters.append(Transaction.created_at >= date_from)
        if date_to is not None:
            filters.append(Transaction.created_at <= date_to)
        return filters

    def list_transactions(
        self,
        *,
        limit: int,
        offset: int,
        transaction_type: TransactionType | None = None,
        status: TransactionStatus | None = None,
        account_id: uuid.UUID | None = None,
        owner_id: uuid.UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Transaction]:
        """List transactions newest first with every supported filter."""
        statement = (
            select(Transaction)
            .where(
                *self._filters(
                    transaction_type=transaction_type,
                    status=status,
                    account_id=account_id,
                    owner_id=owner_id,
                    date_from=date_from,
                    date_to=date_to,
                )
            )
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(statement).all())

    def count_transactions(
        self,
        *,
        transaction_type: TransactionType | None = None,
        status: TransactionStatus | None = None,
        account_id: uuid.UUID | None = None,
        owner_id: uuid.UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        """Count transactions with the same filters as the listing."""
        statement = (
            select(func.count())
            .select_from(Transaction)
            .where(
                *self._filters(
                    transaction_type=transaction_type,
                    status=status,
                    account_id=account_id,
                    owner_id=owner_id,
                    date_from=date_from,
                    date_to=date_to,
                )
            )
        )
        return int(self.session.scalar(statement) or 0)
