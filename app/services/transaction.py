"""Financial operations service with idempotency and auditing."""

# Standard library
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

# Third-party
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Project imports
from app.core.clock import utc_now
from app.core.correlation import get_correlation_id
from app.core.errors import (
    AuthenticationError,
    BankOSError,
    BusinessValidationError,
    IdempotencyConflictError,
    NotFoundError,
)
from app.core.idempotency import (
    IdempotencyLockRegistry,
    IdempotentOutcome,
    WebhookNotification,
    idempotency_expiry,
)
from app.core.logging import get_logger
from app.core.principal import Principal
from app.models.account import Account
from app.models.enums import AccountStatus, IdempotencyStatus, TransactionStatus, TransactionType
from app.models.idempotency import IdempotencyRecord
from app.models.tenant import Tenant
from app.models.transaction import Transaction
from app.repositories.account import AccountRepository
from app.repositories.idempotency import IdempotencyRepository
from app.repositories.tenant import ExchangeRateRepository, TenantRepository
from app.repositories.transaction import TransactionRepository
from app.schemas.common import ApiResponse, Page, success_response
from app.schemas.transaction import (
    DepositRequest,
    TransactionRead,
    TransferPreviewRequest,
    TransferQuote,
    TransferRequest,
    WithdrawalRequest,
)
from app.services.pricing import (
    compute_fee,
    convert_amount,
    ensure_within_limit,
    resolve_exchange_rate,
)

logger = get_logger(__name__)

_LOCKS = IdempotencyLockRegistry()


@dataclass
class OperationContext:
    """Best-effort description of an operation, stored when it fails."""

    transaction_type: TransactionType | None = None
    source_account_id: uuid.UUID | None = None
    target_account_id: uuid.UUID | None = None
    source_account_number: str | None = None
    target_account_number: str | None = None
    amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    target_currency: str | None = None
    description: str | None = None


BuildResult = tuple[ApiResponse[TransactionRead], WebhookNotification | None]


class TransactionService:
    """Execute deposits, withdrawals and transfers inside one tenant."""

    def __init__(self, session: Session, principal: Principal) -> None:
        self.session: Session = session
        self.principal: Principal = principal
        self.tenant: Tenant = self._load_tenant()
        self.accounts: AccountRepository = AccountRepository(session, principal.tenant_id)
        self.rates: ExchangeRateRepository = ExchangeRateRepository(session, principal.tenant_id)
        self.transactions: TransactionRepository = TransactionRepository(
            session, principal.tenant_id
        )
        self.idempotency: IdempotencyRepository = IdempotencyRepository(session)

    # ------------------------------------------------------------------ reads

    def list_history(
        self,
        *,
        limit: int,
        offset: int,
        transaction_type: TransactionType | None,
        status: TransactionStatus | None,
        account_id: uuid.UUID | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> Page[TransactionRead]:
        """Return the paginated history the caller is allowed to see."""
        owner_id = None if self.principal.is_admin else self.principal.user_id
        if account_id is not None and owner_id is not None:
            self._visible_account(account_id)
        transactions = self.transactions.list_transactions(
            limit=limit,
            offset=offset,
            transaction_type=transaction_type,
            status=status,
            account_id=account_id,
            owner_id=owner_id,
            date_from=date_from,
            date_to=date_to,
        )
        total = self.transactions.count_transactions(
            transaction_type=transaction_type,
            status=status,
            account_id=account_id,
            owner_id=owner_id,
            date_from=date_from,
            date_to=date_to,
        )
        return Page[TransactionRead](
            items=[TransactionRead.model_validate(item) for item in transactions],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get(self, transaction_id: uuid.UUID) -> TransactionRead:
        """Return one transaction the caller can see."""
        transaction = self.transactions.get(transaction_id)
        if transaction is None:
            raise NotFoundError("Transaction", str(transaction_id))
        if not self.principal.is_admin:
            visible = any(
                account_id is not None and self._owns(account_id)
                for account_id in (
                    transaction.source_account_id,
                    transaction.target_account_id,
                )
            )
            if not visible:
                raise NotFoundError("Transaction", str(transaction_id))
        return TransactionRead.model_validate(transaction)

    def quote(self, payload: TransferPreviewRequest) -> TransferQuote:
        """Preview fee, rate and converted amount without moving funds."""
        source = self._visible_account(payload.source_account_id)
        target = self._target_account(payload.target_account_number)
        self._ensure_operable(source)
        self._ensure_operable(target)
        self._ensure_distinct(source, target)
        ensure_within_limit(self.tenant, payload.amount)

        fee = compute_fee(self.tenant, payload.amount)
        rate = resolve_exchange_rate(self.rates, source.currency, target.currency)
        return TransferQuote(
            amount=payload.amount,
            fee=fee,
            total_debit=payload.amount + fee,
            exchange_rate=rate,
            converted_amount=convert_amount(payload.amount, rate),
            source_currency=source.currency,
            target_currency=target.currency,
        )

    # ------------------------------------------------------------- operations

    def deposit(
        self, account_id: uuid.UUID, payload: DepositRequest, idempotency_key: str
    ) -> IdempotentOutcome:
        """Credit an account exactly once for a given idempotency key."""

        def build(context: OperationContext) -> BuildResult:
            account = self._visible_account(account_id)
            context.transaction_type = TransactionType.DEPOSIT
            context.target_account_id = account.id
            context.target_account_number = account.account_number
            context.amount = payload.amount
            context.currency = account.currency
            context.description = payload.description
            self._ensure_operable(account)
            ensure_within_limit(self.tenant, payload.amount)

            account.balance = Decimal(account.balance) + payload.amount
            transaction = Transaction(
                tenant_id=self.principal.tenant_id,
                actor_user_id=self.principal.user_id,
                transaction_type=TransactionType.DEPOSIT,
                status=TransactionStatus.SUCCESS,
                target_account_id=account.id,
                target_account_number=account.account_number,
                amount=payload.amount,
                currency=account.currency,
                converted_amount=payload.amount,
                target_currency=account.currency,
                exchange_rate=Decimal("1.000000"),
                fee=Decimal("0.00"),
                description=payload.description,
                idempotency_key=idempotency_key,
            )
            self.session.add(transaction)
            self.session.flush()
            body = success_response(
                TransactionRead.model_validate(transaction),
                message="Deposit completed",
                code="DEPOSIT_COMPLETED",
            )
            return body, None

        return self._execute(idempotency_key, 201, build)

    def withdraw(
        self, account_id: uuid.UUID, payload: WithdrawalRequest, idempotency_key: str
    ) -> IdempotentOutcome:
        """Debit an account exactly once for a given idempotency key."""

        def build(context: OperationContext) -> BuildResult:
            account = self._visible_account(account_id)
            context.transaction_type = TransactionType.WITHDRAWAL
            context.source_account_id = account.id
            context.source_account_number = account.account_number
            context.amount = payload.amount
            context.currency = account.currency
            context.description = payload.description
            self._ensure_operable(account)
            ensure_within_limit(self.tenant, payload.amount)
            if Decimal(account.balance) < payload.amount:
                raise BusinessValidationError(
                    "The account does not have enough funds",
                    code="INSUFFICIENT_FUNDS",
                    details={
                        "balance": format(Decimal(account.balance), "f"),
                        "required": format(payload.amount, "f"),
                        "currency": account.currency,
                    },
                )

            account.balance = Decimal(account.balance) - payload.amount
            transaction = Transaction(
                tenant_id=self.principal.tenant_id,
                actor_user_id=self.principal.user_id,
                transaction_type=TransactionType.WITHDRAWAL,
                status=TransactionStatus.SUCCESS,
                source_account_id=account.id,
                source_account_number=account.account_number,
                amount=payload.amount,
                currency=account.currency,
                converted_amount=payload.amount,
                target_currency=account.currency,
                exchange_rate=Decimal("1.000000"),
                fee=Decimal("0.00"),
                description=payload.description,
                idempotency_key=idempotency_key,
            )
            self.session.add(transaction)
            self.session.flush()
            body = success_response(
                TransactionRead.model_validate(transaction),
                message="Withdrawal completed",
                code="WITHDRAWAL_COMPLETED",
            )
            return body, None

        return self._execute(idempotency_key, 201, build)

    def transfer(self, payload: TransferRequest, idempotency_key: str) -> IdempotentOutcome:
        """Transfer funds between accounts of the tenant exactly once."""

        def build(context: OperationContext) -> BuildResult:
            source = self._visible_account(payload.source_account_id)
            target = self._target_account(payload.target_account_number)
            context.transaction_type = TransactionType.TRANSFER
            context.source_account_id = source.id
            context.source_account_number = source.account_number
            context.target_account_id = target.id
            context.target_account_number = target.account_number
            context.amount = payload.amount
            context.currency = source.currency
            context.target_currency = target.currency
            context.description = payload.description

            self._ensure_operable(source)
            self._ensure_operable(target)
            self._ensure_distinct(source, target)
            ensure_within_limit(self.tenant, payload.amount)

            fee = compute_fee(self.tenant, payload.amount)
            total_debit = payload.amount + fee
            if Decimal(source.balance) < total_debit:
                raise BusinessValidationError(
                    "The source account does not have enough funds to cover the amount and fee",
                    code="INSUFFICIENT_FUNDS",
                    details={
                        "balance": format(Decimal(source.balance), "f"),
                        "amount": format(payload.amount, "f"),
                        "fee": format(fee, "f"),
                        "required": format(total_debit, "f"),
                        "currency": source.currency,
                    },
                )

            rate = resolve_exchange_rate(self.rates, source.currency, target.currency)
            converted = convert_amount(payload.amount, rate)

            source.balance = Decimal(source.balance) - total_debit
            target.balance = Decimal(target.balance) + converted
            transaction = Transaction(
                tenant_id=self.principal.tenant_id,
                actor_user_id=self.principal.user_id,
                transaction_type=TransactionType.TRANSFER,
                status=TransactionStatus.SUCCESS,
                source_account_id=source.id,
                target_account_id=target.id,
                source_account_number=source.account_number,
                target_account_number=target.account_number,
                amount=payload.amount,
                currency=source.currency,
                converted_amount=converted,
                target_currency=target.currency,
                exchange_rate=rate,
                fee=fee,
                description=payload.description,
                idempotency_key=idempotency_key,
            )
            self.session.add(transaction)
            self.session.flush()

            body = success_response(
                TransactionRead.model_validate(transaction),
                message="Transfer completed",
                code="TRANSFER_COMPLETED",
            )
            return body, self._notification(transaction)

        return self._execute(idempotency_key, 201, build)

    # ------------------------------------------------------------ idempotency

    def _execute(
        self,
        idempotency_key: str,
        status_code: int,
        build: Callable[[OperationContext], BuildResult],
    ) -> IdempotentOutcome:
        """Run a financial operation at most once per key, replaying results."""
        context = OperationContext()
        scope = (self.principal.tenant_id, self.principal.user_id, idempotency_key)

        with _LOCKS.acquire(*scope):
            self.idempotency.delete_expired(utc_now())
            record = self.idempotency.get(*scope)
            if record is not None and _as_aware(record.expires_at) <= utc_now():
                self.session.delete(record)
                self.session.commit()
                record = None

            if record is not None:
                if (
                    record.status is IdempotencyStatus.COMPLETED
                    and record.response_body is not None
                ):
                    return IdempotentOutcome(
                        body=record.response_body,
                        status_code=record.response_status or status_code,
                        replayed=True,
                    )
                raise IdempotencyConflictError(
                    "A transaction with this Idempotency-Key is already in progress"
                )

            record = IdempotencyRecord(
                tenant_id=self.principal.tenant_id,
                user_id=self.principal.user_id,
                key=idempotency_key,
                status=IdempotencyStatus.IN_PROGRESS,
                expires_at=idempotency_expiry(),
            )
            self.session.add(record)
            try:
                self.session.commit()
            except IntegrityError:
                self.session.rollback()
                existing = self.idempotency.get(*scope)
                if existing is not None and existing.response_body is not None:
                    return IdempotentOutcome(
                        body=existing.response_body,
                        status_code=existing.response_status or status_code,
                        replayed=True,
                    )
                raise IdempotencyConflictError(
                    "A transaction with this Idempotency-Key is already in progress"
                ) from None

            try:
                response, notification = build(context)
                body = response.model_dump(mode="json")
                stored = self.idempotency.get(*scope)
                if stored is None:
                    raise IdempotencyConflictError(
                        "The idempotency record disappeared while processing the request"
                    )
                stored.status = IdempotencyStatus.COMPLETED
                stored.response_status = status_code
                stored.response_body = body
                self.session.commit()
                return IdempotentOutcome(
                    body=body,
                    status_code=status_code,
                    notification=notification,
                )
            except BankOSError as exc:
                self.session.rollback()
                self._record_failure(idempotency_key, context, exc.code)
                raise
            except Exception:
                self.session.rollback()
                self._release_key(idempotency_key)
                raise

    def _record_failure(
        self, idempotency_key: str, context: OperationContext, error_code: str
    ) -> None:
        """Persist the failed attempt and release the key for a later retry."""
        try:
            record = self.idempotency.get(
                self.principal.tenant_id, self.principal.user_id, idempotency_key
            )
            if record is not None:
                self.session.delete(record)
            if context.transaction_type is None:
                self.session.commit()
                return
            self.session.add(
                Transaction(
                    tenant_id=self.principal.tenant_id,
                    actor_user_id=self.principal.user_id,
                    transaction_type=context.transaction_type,
                    status=TransactionStatus.ERROR,
                    source_account_id=context.source_account_id,
                    target_account_id=context.target_account_id,
                    source_account_number=context.source_account_number,
                    target_account_number=context.target_account_number,
                    amount=context.amount,
                    currency=context.currency,
                    converted_amount=Decimal("0.00"),
                    target_currency=context.target_currency or context.currency,
                    exchange_rate=Decimal("1.000000"),
                    fee=Decimal("0.00"),
                    description=context.description,
                    idempotency_key=idempotency_key,
                    error_code=error_code,
                )
            )
            self.session.commit()
        except Exception:  # pragma: no cover - never mask the original error
            self.session.rollback()
            logger.exception("Could not persist the failed transaction")

    def _release_key(self, idempotency_key: str) -> None:
        """Forget a key after an unexpected error so the caller can retry."""
        try:
            record = self.idempotency.get(
                self.principal.tenant_id, self.principal.user_id, idempotency_key
            )
            if record is not None:
                self.session.delete(record)
                self.session.commit()
        except Exception:  # pragma: no cover - never mask the original error
            self.session.rollback()
            logger.exception("Could not release the idempotency key")

    # ----------------------------------------------------------------- helpers

    def _load_tenant(self) -> Tenant:
        tenant = TenantRepository(self.session).get(self.principal.tenant_id)
        if tenant is None or not tenant.is_active:
            raise AuthenticationError("The tenant is not active")
        return tenant

    def _visible_account(self, account_id: uuid.UUID) -> Account:
        account = self.accounts.get(account_id)
        if account is None:
            raise NotFoundError("Account", str(account_id))
        if not self.principal.is_admin and account.owner_id != self.principal.user_id:
            raise NotFoundError("Account", str(account_id))
        return account

    def _owns(self, account_id: uuid.UUID) -> bool:
        account = self.accounts.get(account_id)
        return account is not None and account.owner_id == self.principal.user_id

    def _target_account(self, account_number: str) -> Account:
        account = self.accounts.get_by_number(account_number)
        if account is None:
            raise NotFoundError("Account", account_number)
        return account

    @staticmethod
    def _ensure_operable(account: Account) -> None:
        if account.status is not AccountStatus.ACTIVE:
            raise BusinessValidationError(
                "The account is not active",
                code="ACCOUNT_NOT_ACTIVE",
                details={"account_id": str(account.id), "status": account.status.value},
            )

    @staticmethod
    def _ensure_distinct(source: Account, target: Account) -> None:
        if source.id == target.id:
            raise BusinessValidationError(
                "The source and target accounts must be different",
                code="SAME_ACCOUNT_TRANSFER",
            )

    def _notification(self, transaction: Transaction) -> WebhookNotification | None:
        if not self.tenant.webhook_url:
            return None
        return WebhookNotification(
            url=self.tenant.webhook_url,
            payload={
                "event": "transfer.received",
                "tenant_id": str(self.tenant.id),
                "tenant_slug": self.tenant.slug,
                "transaction_id": str(transaction.id),
                "source_account_number": transaction.source_account_number,
                "target_account_number": transaction.target_account_number,
                "amount": format(transaction.amount, "f"),
                "currency": transaction.currency,
                "converted_amount": format(transaction.converted_amount, "f"),
                "target_currency": transaction.target_currency,
                "exchange_rate": format(transaction.exchange_rate, "f"),
                "fee": format(transaction.fee, "f"),
                "description": transaction.description,
                "occurred_at": transaction.created_at.isoformat(),
            },
            correlation_id=get_correlation_id(),
        )


def _as_aware(value: datetime) -> datetime:
    """Treat stored naive timestamps as UTC for Python-side comparisons."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
