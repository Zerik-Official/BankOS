"""Account endpoints and single-account financial operations."""

# Standard library
import uuid

# Third-party
from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query, status
from fastapi.responses import JSONResponse

# Project imports
from app.api.dependencies import (
    Pagination,
    enforce_financial_rate_limit,
    get_account_service,
    get_admin_principal,
    get_pagination,
    get_principal,
    get_transaction_service,
)
from app.api.responses import idempotent_response
from app.core.idempotency import validate_idempotency_key
from app.core.principal import Principal
from app.models.enums import AccountStatus
from app.schemas.account import AccountCreateRequest, AccountRead, AccountStatusUpdateRequest
from app.schemas.common import ApiResponse, Page, success_response
from app.schemas.transaction import (
    DepositRequest,
    TransactionRead,
    WithdrawalRequest,
)
from app.services.account import AccountService
from app.services.transaction import TransactionService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post(
    "",
    response_model=ApiResponse[AccountRead],
    status_code=status.HTTP_201_CREATED,
    summary="Open an account for a client",
)
def create_account(
    payload: AccountCreateRequest,
    principal: Principal = Depends(get_admin_principal),
    service: AccountService = Depends(get_account_service),
) -> ApiResponse[AccountRead]:
    """Create a zero-balance account in the requested currency."""
    account = service.create(payload)
    return success_response(account, message="Account created", code="ACCOUNT_CREATED")


@router.get(
    "",
    response_model=ApiResponse[Page[AccountRead]],
    summary="List accounts",
)
def list_accounts(
    pagination: Pagination = Depends(get_pagination),
    owner_id: uuid.UUID | None = Query(default=None, description="Filter by owner"),
    account_status: AccountStatus | None = Query(default=None, alias="status"),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
    principal: Principal = Depends(get_principal),
    service: AccountService = Depends(get_account_service),
) -> ApiResponse[Page[AccountRead]]:
    """Return a page of accounts; clients only see their own."""
    page = service.list_accounts(
        limit=pagination.limit,
        offset=pagination.offset,
        owner_id=owner_id,
        status=account_status,
        currency=currency.upper() if currency else None,
    )
    return success_response(page, code="ACCOUNT_LIST")


@router.get(
    "/{account_id}",
    response_model=ApiResponse[AccountRead],
    summary="Read an account",
)
def read_account(
    account_id: uuid.UUID,
    service: AccountService = Depends(get_account_service),
) -> ApiResponse[AccountRead]:
    """Return the balance and state of one account."""
    return success_response(service.get(account_id), code="ACCOUNT_DETAIL")


@router.patch(
    "/{account_id}/status",
    response_model=ApiResponse[AccountRead],
    summary="Change the state of an account",
)
def update_account_status(
    account_id: uuid.UUID,
    payload: AccountStatusUpdateRequest,
    principal: Principal = Depends(get_admin_principal),
    service: AccountService = Depends(get_account_service),
) -> ApiResponse[AccountRead]:
    """Deactivate or block an account without deleting its history."""
    account = service.update_status(account_id, payload)
    return success_response(
        account, message="Account status updated", code="ACCOUNT_STATUS_UPDATED"
    )


@router.post(
    "/{account_id}/deposits",
    response_model=ApiResponse[TransactionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Deposit money into an account",
    dependencies=[Depends(enforce_financial_rate_limit)],
)
def deposit(
    account_id: uuid.UUID,
    payload: DepositRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: TransactionService = Depends(get_transaction_service),
) -> JSONResponse:
    """Credit an account exactly once per idempotency key."""
    key = validate_idempotency_key(idempotency_key)
    return idempotent_response(service.deposit(account_id, payload, key), background_tasks)


@router.post(
    "/{account_id}/withdrawals",
    response_model=ApiResponse[TransactionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Withdraw money from an account",
    dependencies=[Depends(enforce_financial_rate_limit)],
)
def withdraw(
    account_id: uuid.UUID,
    payload: WithdrawalRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: TransactionService = Depends(get_transaction_service),
) -> JSONResponse:
    """Debit an account exactly once per idempotency key."""
    key = validate_idempotency_key(idempotency_key)
    return idempotent_response(service.withdraw(account_id, payload, key), background_tasks)
