"""Seed idempotent demo data for BankOS."""

# Standard library
import uuid
from dataclasses import dataclass
from decimal import Decimal

# Third-party
from sqlalchemy import select
from sqlalchemy.orm import Session

# Project imports
from app.core.principal import Principal
from app.core.security import hash_password, verify_password
from app.db.session import SessionLocal, create_schema
from app.models.account import Account
from app.models.enums import AccountStatus, CommissionType, TransactionStatus, UserRole
from app.models.tenant import Tenant
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.account import AccountRepository
from app.repositories.tenant import ExchangeRateRepository, TenantRepository
from app.repositories.user import UserRepository
from app.schemas.account import AccountCreateRequest, AccountStatusUpdateRequest
from app.schemas.tenant import (
    ExchangeRateBulkRequest,
    ExchangeRateItem,
    TenantRegisterRequest,
)
from app.schemas.transaction import DepositRequest
from app.schemas.user import UserCreateRequest
from app.services.account import AccountService
from app.services.tenant import TenantService
from app.services.transaction import TransactionService
from app.services.user import UserService

DEMO_PASSWORD = "DemoPass123"
INITIAL_BASE_BALANCE = Decimal("1000.00")
INITIAL_OTHER_BALANCE = Decimal("500.00")


@dataclass(frozen=True)
class DemoTenant:
    """Configuration of one demo tenant."""

    slug: str
    name: str
    base_currency: str
    other_currency: str
    commission_type: CommissionType
    commission_value: Decimal


DEMO_TENANTS: tuple[DemoTenant, ...] = (
    DemoTenant(
        slug="acme",
        name="Acme Demo Bank",
        base_currency="USD",
        other_currency="EUR",
        commission_type=CommissionType.PERCENTAGE,
        commission_value=Decimal("2"),
    ),
    DemoTenant(
        slug="globex",
        name="Globex Demo Bank",
        base_currency="EUR",
        other_currency="USD",
        commission_type=CommissionType.FIXED,
        commission_value=Decimal("1.50"),
    ),
)

DEMO_CLIENTS: tuple[tuple[str, str], ...] = (
    ("alice", "Alice Demo"),
    ("bob", "Bob Demo"),
)

DEMO_RATES: tuple[tuple[str, str, Decimal], ...] = (
    ("USD", "EUR", Decimal("0.900000")),
    ("EUR", "USD", Decimal("1.100000")),
)


def _admin_principal(admin: User) -> Principal:
    """Build the administrator principal used by the services."""
    return Principal(
        user_id=admin.id,
        tenant_id=admin.tenant_id,
        role=UserRole.ADMINISTRATOR,
        email=admin.email,
        full_name=admin.full_name,
    )


def _ensure_password(session: Session, user: User) -> None:
    """Keep the documented demo password valid for an existing user."""
    if verify_password(DEMO_PASSWORD, user.password_hash):
        return
    user.password_hash = hash_password(DEMO_PASSWORD)
    session.commit()


def _ensure_tenant(session: Session, config: DemoTenant) -> tuple[Tenant, User]:
    """Create the demo tenant and its administrator when missing."""
    tenants = TenantRepository(session)
    tenant = tenants.get_by_slug(config.slug)
    if tenant is None:
        TenantService(session).register(
            TenantRegisterRequest(
                name=config.name,
                slug=config.slug,
                admin_email=f"admin@{config.slug}.demo",
                admin_full_name="Demo Administrator",
                admin_password=DEMO_PASSWORD,
                base_currency=config.base_currency,
                commission_type=config.commission_type,
                commission_value=config.commission_value,
            )
        )
        tenant = tenants.get_by_slug(config.slug)

    if tenant is None:
        raise RuntimeError(f"Could not create the demo tenant {config.slug}")

    admin = UserRepository(session, tenant.id).get_by_email(f"admin@{config.slug}.demo")
    if admin is None:
        raise RuntimeError(f"The demo tenant {config.slug} has no administrator")
    _ensure_password(session, admin)
    return tenant, admin


def _ensure_rates(session: Session, tenant: Tenant, principal: Principal) -> None:
    """Install the static demo rates without duplicating the table."""
    repository = ExchangeRateRepository(session, tenant.id)
    current = {
        (rate.source_currency, rate.target_currency): Decimal(rate.rate)
        for rate in repository.list_all()
    }
    desired = {(source, target): rate for source, target, rate in DEMO_RATES}
    if current == desired:
        return
    TenantService(session).replace_rates(
        principal,
        ExchangeRateBulkRequest(
            rates=[
                ExchangeRateItem(source_currency=source, target_currency=target, rate=rate)
                for source, target, rate in DEMO_RATES
            ]
        ),
    )


def _ensure_client(
    session: Session,
    tenant: Tenant,
    principal: Principal,
    email: str,
    full_name: str,
) -> User:
    """Create or reuse an active demo client."""
    repository = UserRepository(session, tenant.id)
    user = repository.get_by_email(email)
    if user is None:
        created = UserService(session, principal).create(
            UserCreateRequest(
                email=email,
                full_name=full_name,
                password=DEMO_PASSWORD,
                role=UserRole.CLIENT,
            )
        )
        user = repository.get(created.id)
        if user is None:
            raise RuntimeError(f"Could not create the demo client {email}")
    elif user.role is not UserRole.CLIENT or not user.is_active:
        user.role = UserRole.CLIENT
        user.is_active = True
        session.commit()

    _ensure_password(session, user)
    return user


def _ensure_account(
    session: Session,
    tenant: Tenant,
    principal: Principal,
    owner: User,
    currency: str,
) -> Account:
    """Create or reuse an active account for the given currency."""
    repository = AccountRepository(session, tenant.id)
    accounts = repository.list_accounts(
        limit=100,
        offset=0,
        owner_id=owner.id,
        currency=currency,
    )
    if accounts:
        account = accounts[0]
    else:
        created = AccountService(session, principal).create(
            AccountCreateRequest(owner_id=owner.id, currency=currency)
        )
        account = repository.get(created.id)
        if account is None:
            raise RuntimeError(f"Could not create the {currency} account of {owner.email}")

    if account.status is not AccountStatus.ACTIVE:
        AccountService(session, principal).update_status(
            account.id,
            AccountStatusUpdateRequest(status=AccountStatus.ACTIVE),
        )
        refreshed = repository.get(account.id)
        if refreshed is None:
            raise RuntimeError(f"Could not reactivate the account {account.account_number}")
        account = refreshed
    return account


def _ensure_initial_deposit(
    session: Session,
    tenant: Tenant,
    principal: Principal,
    account: Account,
    amount: Decimal,
) -> None:
    """Deposit the initial balance once per demo account."""
    key = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"bankos-demo:{tenant.slug}:{account.id}:{account.currency}:initial",
        )
    )
    existing = session.scalars(
        select(Transaction).where(
            Transaction.tenant_id == tenant.id,
            Transaction.idempotency_key == key,
            Transaction.status == TransactionStatus.SUCCESS,
        )
    ).first()
    if existing is not None:
        return
    TransactionService(session, principal).deposit(
        account.id,
        DepositRequest(amount=amount),
        key,
    )


def main() -> None:
    """Create the demo tenants, users, accounts and balances."""
    create_schema()
    lines: list[str] = []

    with SessionLocal() as session:
        for config in DEMO_TENANTS:
            tenant, admin = _ensure_tenant(session, config)
            principal = _admin_principal(admin)
            _ensure_rates(session, tenant, principal)
            lines.append(f"[{tenant.slug}] administrator: {admin.email} / {DEMO_PASSWORD}")
            lines.append(
                f"[{tenant.slug}] commission: {config.commission_type.value} "
                f"{config.commission_value}"
            )

            for username, full_name in DEMO_CLIENTS:
                email = f"{username}@{tenant.slug}.demo"
                client_user = _ensure_client(session, tenant, principal, email, full_name)
                lines.append(f"[{tenant.slug}] client: {client_user.email} / {DEMO_PASSWORD}")

                balances: tuple[tuple[str, Decimal], ...] = (
                    (config.base_currency, INITIAL_BASE_BALANCE),
                    (config.other_currency, INITIAL_OTHER_BALANCE),
                )
                for currency, amount in balances:
                    account = _ensure_account(
                        session,
                        tenant,
                        principal,
                        client_user,
                        currency,
                    )
                    _ensure_initial_deposit(session, tenant, principal, account, amount)
                    session.refresh(account)
                    lines.append(
                        f"[{tenant.slug}] account: {account.account_number} "
                        f"({account.currency}, balance {account.balance:.2f})"
                    )

    print("BankOS demo data is ready.")
    print(f"Demo password for every user: {DEMO_PASSWORD}")
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
