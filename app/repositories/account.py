"""Account repository."""

# Standard library
import uuid

# Third-party
from sqlalchemy import func, select
from sqlalchemy.orm import Session

# Project imports
from app.models.account import Account
from app.models.enums import AccountStatus
from app.repositories.base import TenantScopedRepository


class AccountRepository(TenantScopedRepository[Account]):
    """Persistence for the accounts of one tenant."""

    def __init__(self, session: Session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, Account, tenant_id)

    def get_by_number(self, account_number: str) -> Account | None:
        """Return the account with that number inside the tenant."""
        statement = select(Account).where(
            Account.tenant_id == self.tenant_id,
            Account.account_number == account_number,
        )
        return self.session.scalars(statement).first()

    def list_accounts(
        self,
        *,
        limit: int,
        offset: int,
        owner_id: uuid.UUID | None = None,
        status: AccountStatus | None = None,
        currency: str | None = None,
    ) -> list[Account]:
        """List accounts with optional filters."""
        statement = select(Account).where(Account.tenant_id == self.tenant_id)
        if owner_id is not None:
            statement = statement.where(Account.owner_id == owner_id)
        if status is not None:
            statement = statement.where(Account.status == status)
        if currency is not None:
            statement = statement.where(Account.currency == currency)
        statement = statement.order_by(Account.created_at.desc()).limit(limit).offset(offset)
        return list(self.session.scalars(statement).all())

    def count_accounts(
        self,
        *,
        owner_id: uuid.UUID | None = None,
        status: AccountStatus | None = None,
        currency: str | None = None,
    ) -> int:
        """Count accounts with the same filters as the listing."""
        statement = (
            select(func.count()).select_from(Account).where(Account.tenant_id == self.tenant_id)
        )
        if owner_id is not None:
            statement = statement.where(Account.owner_id == owner_id)
        if status is not None:
            statement = statement.where(Account.status == status)
        if currency is not None:
            statement = statement.where(Account.currency == currency)
        return int(self.session.scalar(statement) or 0)
