"""Exact decimal types stored as scaled integers on SQLite."""

# Standard library
from decimal import ROUND_HALF_UP, Decimal

# Third-party
from sqlalchemy import BigInteger
from sqlalchemy.types import TypeDecorator

_CENT = Decimal("0.01")
_RATE_SCALE = Decimal("1000000")


class Money(TypeDecorator[Decimal]):
    """Store a monetary amount as integer cents and read it back as Decimal."""

    impl = BigInteger
    cache_ok = True

    def process_bind_param(self, value: Decimal | int | None, dialect: object) -> int | None:
        if value is None:
            return None
        amount = Decimal(value).quantize(_CENT, rounding=ROUND_HALF_UP)
        return int(amount * 100)

    def process_result_value(self, value: int | None, dialect: object) -> Decimal | None:
        if value is None:
            return None
        return (Decimal(value) / 100).quantize(_CENT)


class Rate(TypeDecorator[Decimal]):
    """Store a conversion rate or percentage with six decimal places."""

    impl = BigInteger
    cache_ok = True

    def process_bind_param(self, value: Decimal | int | None, dialect: object) -> int | None:
        if value is None:
            return None
        rate = Decimal(value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        return int(rate * _RATE_SCALE)

    def process_result_value(self, value: int | None, dialect: object) -> Decimal | None:
        if value is None:
            return None
        return Decimal(value) / _RATE_SCALE
