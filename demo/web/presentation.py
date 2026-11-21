"""Template configuration and display helpers for the web frontend."""

# Standard library
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Final

# Third-party
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR: Final[Path] = Path(__file__).resolve().parent / "templates"

TRANSACTION_LABELS: Final[dict[str, str]] = {
    "deposit": "Depósito",
    "withdrawal": "Retiro",
    "transfer": "Transferencia",
}

ERROR_MESSAGES: Final[dict[str, str]] = {
    "UNAUTHENTICATED": "Entidad, correo o contraseña incorrectos",
    "INSUFFICIENT_FUNDS": "No tienes fondos suficientes para esta operación",
    "SAME_ACCOUNT_TRANSFER": "No puedes transferir a la misma cuenta",
    "EXCHANGE_RATE_NOT_FOUND": "No hay tipo de cambio entre estas monedas",
    "TRANSACTION_LIMIT_EXCEEDED": "El importe supera el límite permitido",
    "ACCOUNT_NOT_ACTIVE": "La cuenta no está activa",
    "IDEMPOTENCY_IN_PROGRESS": "Esta operación ya se está procesando",
    "RATE_LIMIT_EXCEEDED": "Demasiadas operaciones seguidas. Espera un minuto",
}


def format_money(value: Decimal | str) -> str:
    """Format an amount with exactly two decimals, such as `898.00`."""
    return f"{Decimal(value):.2f}"


def format_datetime(value: datetime) -> str:
    """Format a timestamp for people, such as `17/11/2026 22:10`."""
    return value.strftime("%d/%m/%Y %H:%M")


def transaction_label(kind: str) -> str:
    """Return the Spanish name of a movement type."""
    return TRANSACTION_LABELS.get(kind, "Movimiento")


def error_message(code: str, fallback: str) -> str:
    """Return the Spanish message for an error code, or the backend message."""
    return ERROR_MESSAGES.get(code, fallback)


def is_incoming(
    kind: str, target_number: str | None, source_number: str | None, own: set[str]
) -> bool:
    """Tell whether money arrives at one of the user's accounts."""
    if kind == "deposit":
        return True
    if kind == "withdrawal":
        return False
    receives = target_number is not None and target_number in own
    sends = source_number is not None and source_number in own
    return receives and not sends


def account_name(currency: str) -> str:
    """Return the display name of an account from its currency, since accounts have no name."""
    names = {"EUR": "Cuenta en euros", "USD": "Cuenta en dólares"}
    return names.get(currency, f"Cuenta en {currency}")


def masked_number(account_number: str) -> str:
    """Hide all but the last four digits of an account number."""
    return f"•••• {account_number[-4:]}"


def build_templates() -> Jinja2Templates:
    """Create the template engine with the display filters registered."""
    engine = Jinja2Templates(directory=str(TEMPLATES_DIR))
    engine.env.filters["money"] = format_money
    engine.env.filters["datetime_es"] = format_datetime
    engine.env.filters["transaction_label"] = transaction_label
    engine.env.filters["account_name"] = account_name
    engine.env.filters["masked_number"] = masked_number
    return engine


templates: Final[Jinja2Templates] = build_templates()
