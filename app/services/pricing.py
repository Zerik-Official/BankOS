"""Fee, limit and currency conversion rules."""

# Standard library
from decimal import ROUND_HALF_UP, Decimal

# Project imports
from app.core.errors import BusinessValidationError
from app.models.enums import CommissionType
from app.models.tenant import Tenant
from app.repositories.tenant import ExchangeRateRepository

CENT = Decimal("0.01")
RATE_PRECISION = Decimal("0.000001")


def quantize_money(value: Decimal) -> Decimal:
    """Round a monetary amount to two decimal places."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def compute_fee(tenant: Tenant, amount: Decimal) -> Decimal:
    """Calculate the commission a tenant charges for an outgoing transfer."""
    if tenant.commission_type is CommissionType.FIXED:
        fee = Decimal(tenant.commission_value)
    else:
        fee = Decimal(amount) * Decimal(tenant.commission_value) / Decimal(100)
    return quantize_money(fee)


def ensure_within_limit(tenant: Tenant, amount: Decimal) -> None:
    """Reject amounts above the tenant limit, expressed in the operation currency."""
    if Decimal(amount) > Decimal(tenant.max_transaction_amount):
        raise BusinessValidationError(
            "The amount exceeds the maximum allowed per transaction",
            code="TRANSACTION_LIMIT_EXCEEDED",
            details={
                "amount": format(amount, "f"),
                "max_transaction_amount": format(tenant.max_transaction_amount, "f"),
            },
        )


def resolve_exchange_rate(
    repository: ExchangeRateRepository,
    source_currency: str,
    target_currency: str,
) -> Decimal:
    """Return the configured rate from source to target, or its inverse."""
    if source_currency == target_currency:
        return Decimal("1.000000")

    direct = repository.get_pair(source_currency, target_currency)
    if direct is not None:
        return Decimal(direct.rate)

    inverse = repository.get_pair(target_currency, source_currency)
    if inverse is not None and Decimal(inverse.rate) > 0:
        return (Decimal(1) / Decimal(inverse.rate)).quantize(RATE_PRECISION)

    raise BusinessValidationError(
        "No exchange rate is configured for this currency pair",
        code="EXCHANGE_RATE_NOT_FOUND",
        details={"source_currency": source_currency, "target_currency": target_currency},
    )


def convert_amount(amount: Decimal, rate: Decimal) -> Decimal:
    """Convert an amount with a rate and round it to cents."""
    return quantize_money(Decimal(amount) * Decimal(rate))
