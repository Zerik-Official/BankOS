"""Transaction history endpoints."""

# Standard library
import uuid
from datetime import datetime

# Third-party
from fastapi import APIRouter, Depends, Query

# Project imports
from app.api.dependencies import (
    Pagination,
    get_pagination,
    get_principal,
    get_transaction_service,
)
from app.core.principal import Principal
from app.models.enums import TransactionStatus, TransactionType
from app.schemas.common import ApiResponse, Page, success_response
from app.schemas.transaction import TransactionRead
from app.services.transaction import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get(
    "",
    response_model=ApiResponse[Page[TransactionRead]],
    summary="List the transaction history",
)
def list_transactions(
    pagination: Pagination = Depends(get_pagination),
    transaction_type: TransactionType | None = Query(default=None, alias="type"),
    transaction_status: TransactionStatus | None = Query(default=None, alias="status"),
    account_id: uuid.UUID | None = Query(default=None, description="Filter by account"),
    date_from: datetime | None = Query(default=None, description="Inclusive lower bound"),
    date_to: datetime | None = Query(default=None, description="Inclusive upper bound"),
    principal: Principal = Depends(get_principal),
    service: TransactionService = Depends(get_transaction_service),
) -> ApiResponse[Page[TransactionRead]]:
    """Return a filtered page of movements; clients only see their own accounts."""
    page = service.list_history(
        limit=pagination.limit,
        offset=pagination.offset,
        transaction_type=transaction_type,
        status=transaction_status,
        account_id=account_id,
        date_from=date_from,
        date_to=date_to,
    )
    return success_response(page, code="TRANSACTION_LIST")


@router.get(
    "/{transaction_id}",
    response_model=ApiResponse[TransactionRead],
    summary="Read a transaction",
)
def read_transaction(
    transaction_id: uuid.UUID,
    principal: Principal = Depends(get_principal),
    service: TransactionService = Depends(get_transaction_service),
) -> ApiResponse[TransactionRead]:
    """Return one transaction the caller is allowed to see."""
    return success_response(service.get(transaction_id), code="TRANSACTION_DETAIL")
