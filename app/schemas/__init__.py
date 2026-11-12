"""Pydantic schemas."""

# Project imports
from app.schemas.account import AccountCreateRequest, AccountRead, AccountStatusUpdateRequest
from app.schemas.audit import AuditLogRead
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import ApiResponse, ErrorResponse, Page, success_response
from app.schemas.tenant import (
    ExchangeRateBulkRequest,
    ExchangeRateRead,
    TenantRead,
    TenantRegisterRequest,
    TenantRegisterResponse,
    TenantUpdateRequest,
)
from app.schemas.transaction import (
    DepositRequest,
    TransactionRead,
    TransferPreviewRequest,
    TransferQuote,
    TransferRequest,
    WithdrawalRequest,
)
from app.schemas.user import UserCreateRequest, UserRead, UserUpdateRequest

__all__ = [
    "AccountCreateRequest",
    "AccountRead",
    "AccountStatusUpdateRequest",
    "ApiResponse",
    "AuditLogRead",
    "DepositRequest",
    "ErrorResponse",
    "ExchangeRateBulkRequest",
    "ExchangeRateRead",
    "LoginRequest",
    "Page",
    "TenantRead",
    "TenantRegisterRequest",
    "TenantRegisterResponse",
    "TenantUpdateRequest",
    "TokenResponse",
    "TransactionRead",
    "TransferPreviewRequest",
    "TransferQuote",
    "TransferRequest",
    "UserCreateRequest",
    "UserRead",
    "UserUpdateRequest",
    "WithdrawalRequest",
    "success_response",
]
