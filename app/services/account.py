"""Account management service."""

# Standard library
import secrets
import uuid
from decimal import Decimal

# Third-party
from sqlalchemy.orm import Session

# Project imports
from app.core.errors import BusinessValidationError, NotFoundError
from app.core.principal import Principal, ensure_admin
from app.models.account import Account
from app.models.enums import AccountStatus, UserRole
from app.repositories.account import AccountRepository
from app.repositories.user import UserRepository
from app.schemas.account import AccountCreateRequest, AccountRead, AccountStatusUpdateRequest
from app.schemas.common import Page
from app.services.audit import AuditService


class AccountService:
    """Open and manage the accounts of a tenant."""

    def __init__(self, session: Session, principal: Principal) -> None:
        self.session: Session = session
        self.principal: Principal = principal
        self.accounts: AccountRepository = AccountRepository(session, principal.tenant_id)
        self.users: UserRepository = UserRepository(session, principal.tenant_id)

    def create(self, payload: AccountCreateRequest) -> AccountRead:
        """Open an account for a client of the tenant."""
        ensure_admin(self.principal)
        owner = self.users.get(payload.owner_id)
        if owner is None:
            raise NotFoundError("User", str(payload.owner_id))
        if owner.role is not UserRole.CLIENT:
            raise BusinessValidationError(
                "Accounts can only be owned by users with the client role",
                code="INVALID_ACCOUNT_OWNER",
                details={"owner_id": str(owner.id), "role": owner.role.value},
            )
        if not owner.is_active:
            raise BusinessValidationError(
                "The owner of the account must be active",
                code="INACTIVE_ACCOUNT_OWNER",
                details={"owner_id": str(owner.id)},
            )

        account = Account(
            tenant_id=self.principal.tenant_id,
            owner_id=owner.id,
            account_number=self._generate_account_number(),
            balance=Decimal("0.00"),
            currency=payload.currency,
            status=AccountStatus.ACTIVE,
        )
        self.session.add(account)
        self.session.flush()
        AuditService(self.session, self.principal.tenant_id).record(
            actor_user_id=self.principal.user_id,
            action="account.created",
            entity_type="account",
            entity_id=str(account.id),
            new_state={
                "account_number": account.account_number,
                "owner_id": str(account.owner_id),
                "currency": account.currency,
                "status": account.status.value,
            },
        )
        self.session.commit()
        return AccountRead.model_validate(account)

    def list_accounts(
        self,
        *,
        limit: int,
        offset: int,
        owner_id: uuid.UUID | None,
        status: AccountStatus | None,
        currency: str | None,
    ) -> Page[AccountRead]:
        """List accounts; clients only see their own."""
        scoped_owner = owner_id
        if not self.principal.is_admin:
            scoped_owner = self.principal.user_id
        accounts = self.accounts.list_accounts(
            limit=limit,
            offset=offset,
            owner_id=scoped_owner,
            status=status,
            currency=currency,
        )
        total = self.accounts.count_accounts(
            owner_id=scoped_owner, status=status, currency=currency
        )
        return Page[AccountRead](
            items=[AccountRead.model_validate(account) for account in accounts],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get(self, account_id: uuid.UUID) -> AccountRead:
        """Return one account when the caller may see it."""
        return AccountRead.model_validate(self.get_visible(account_id))

    def get_visible(self, account_id: uuid.UUID) -> Account:
        """Load an account ensuring tenant isolation and client ownership."""
        account = self.get_for_tenant(account_id)
        if not self.principal.is_admin and account.owner_id != self.principal.user_id:
            raise NotFoundError("Account", str(account_id))
        return account

    def get_for_tenant(self, account_id: uuid.UUID) -> Account:
        """Load an account of the tenant or raise not found."""
        account = self.accounts.get(account_id)
        if account is None:
            raise NotFoundError("Account", str(account_id))
        return account

    def update_status(
        self, account_id: uuid.UUID, payload: AccountStatusUpdateRequest
    ) -> AccountRead:
        """Deactivate, block or reactivate an account without deleting it."""
        ensure_admin(self.principal)
        account = self.get_for_tenant(account_id)
        previous = {"status": account.status}
        account.status = payload.status
        AuditService(self.session, self.principal.tenant_id).record(
            actor_user_id=self.principal.user_id,
            action="account.status.updated",
            entity_type="account",
            entity_id=str(account.id),
            previous_state=previous,
            new_state={"status": account.status.value, "account_number": account.account_number},
        )
        self.session.commit()
        return AccountRead.model_validate(account)

    def _generate_account_number(self) -> str:
        for _ in range(10):
            candidate = f"{secrets.randbelow(10**12):012d}"
            if self.accounts.get_by_number(candidate) is None:
                return candidate
        raise BusinessValidationError(
            "Could not allocate a unique account number",
            code="ACCOUNT_NUMBER_EXHAUSTED",
        )
