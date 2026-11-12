"""Tenant registration and configuration endpoints."""

# Third-party
from fastapi import APIRouter, Depends, status

# Project imports
from app.api.dependencies import get_admin_principal, get_principal, get_tenant_service
from app.core.principal import Principal
from app.schemas.common import ApiResponse, success_response
from app.schemas.tenant import (
    ExchangeRateBulkRequest,
    ExchangeRateRead,
    TenantRead,
    TenantRegisterRequest,
    TenantRegisterResponse,
    TenantUpdateRequest,
)
from app.services.tenant import TenantService

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post(
    "",
    response_model=ApiResponse[TenantRegisterResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a tenant with its first administrator",
)
def register_tenant(
    payload: TenantRegisterRequest,
    service: TenantService = Depends(get_tenant_service),
) -> ApiResponse[TenantRegisterResponse]:
    """Create an isolated tenant and its administrator account."""
    registered = service.register(payload)
    return success_response(registered, message="Tenant created", code="TENANT_REGISTERED")


@router.get(
    "/me",
    response_model=ApiResponse[TenantRead],
    summary="Read the current tenant configuration",
)
def read_current_tenant(
    principal: Principal = Depends(get_principal),
    service: TenantService = Depends(get_tenant_service),
) -> ApiResponse[TenantRead]:
    """Return the configuration of the tenant encoded in the token."""
    return success_response(service.get_current(principal), code="TENANT_CONFIG")


@router.patch(
    "/me",
    response_model=ApiResponse[TenantRead],
    summary="Update the current tenant configuration",
)
def update_current_tenant(
    payload: TenantUpdateRequest,
    principal: Principal = Depends(get_admin_principal),
    service: TenantService = Depends(get_tenant_service),
) -> ApiResponse[TenantRead]:
    """Update limits, commission or webhook of the tenant and audit the change."""
    updated = service.update(principal, payload)
    return success_response(updated, message="Tenant updated", code="TENANT_UPDATED")


@router.get(
    "/me/exchange-rates",
    response_model=ApiResponse[list[ExchangeRateRead]],
    summary="List the static exchange rates",
)
def list_exchange_rates(
    principal: Principal = Depends(get_principal),
    service: TenantService = Depends(get_tenant_service),
) -> ApiResponse[list[ExchangeRateRead]]:
    """Return the rate table used for multi-currency transfers."""
    return success_response(service.list_rates(principal), code="EXCHANGE_RATES")


@router.put(
    "/me/exchange-rates",
    response_model=ApiResponse[list[ExchangeRateRead]],
    summary="Replace the static exchange rates",
)
def replace_exchange_rates(
    payload: ExchangeRateBulkRequest,
    principal: Principal = Depends(get_admin_principal),
    service: TenantService = Depends(get_tenant_service),
) -> ApiResponse[list[ExchangeRateRead]]:
    """Replace the whole rate table of the tenant and audit the change."""
    rates = service.replace_rates(principal, payload)
    return success_response(rates, message="Exchange rates replaced", code="EXCHANGE_RATES_UPDATED")
