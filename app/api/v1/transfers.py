"""Transfer endpoints."""

# Third-party
from fastapi import APIRouter, BackgroundTasks, Depends, Header, status
from fastapi.responses import JSONResponse

# Project imports
from app.api.dependencies import (
    enforce_financial_rate_limit,
    get_principal,
    get_transaction_service,
)
from app.api.responses import idempotent_response
from app.core.idempotency import validate_idempotency_key
from app.core.principal import Principal
from app.schemas.common import ApiResponse, success_response
from app.schemas.transaction import (
    TransactionRead,
    TransferPreviewRequest,
    TransferQuote,
    TransferRequest,
)
from app.services.transaction import TransactionService

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post(
    "/quote",
    response_model=ApiResponse[TransferQuote],
    summary="Preview a transfer",
)
def quote_transfer(
    payload: TransferPreviewRequest,
    principal: Principal = Depends(get_principal),
    service: TransactionService = Depends(get_transaction_service),
) -> ApiResponse[TransferQuote]:
    """Return fee, exchange rate and converted amount without moving funds."""
    return success_response(
        service.quote(payload), message="Transfer quoted", code="TRANSFER_QUOTE"
    )


@router.post(
    "",
    response_model=ApiResponse[TransactionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Transfer money between accounts",
    dependencies=[Depends(enforce_financial_rate_limit)],
)
def create_transfer(
    payload: TransferRequest,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: TransactionService = Depends(get_transaction_service),
) -> JSONResponse:
    """Move funds between accounts of the tenant, charging the configured commission."""
    key = validate_idempotency_key(idempotency_key)
    return idempotent_response(service.transfer(payload, key), background_tasks)
