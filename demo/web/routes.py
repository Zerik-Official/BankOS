"""Pages of the BankOS web frontend.

Each page calls the same services as the REST API, so the rules (tenant
isolation, roles, idempotency and business checks) live in one place.
"""

# Standard library
import uuid
from typing import Final
from urllib.parse import urlencode

# Third-party
from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

# Project imports
from app.api.dependencies import get_session
from app.core.errors import AuthenticationError, BankOSError
from app.core.idempotency import validate_idempotency_key
from app.core.principal import Principal
from app.models.enums import AccountStatus, TransactionType
from app.repositories.tenant import TenantRepository
from app.schemas.account import AccountRead
from app.schemas.auth import LoginRequest
from app.schemas.transaction import (
    DepositRequest,
    TransactionRead,
    TransferPreviewRequest,
    TransferQuote,
    TransferRequest,
    WithdrawalRequest,
)
from app.services.account import AccountService
from app.services.auth import AuthService
from app.services.transaction import TransactionService
from demo.web.auth import SESSION_COOKIE, LoginRequiredError, get_web_principal
from demo.web.presentation import error_message, is_incoming, templates

router = APIRouter(include_in_schema=False)

HISTORY_PAGE_SIZE: Final[int] = 20
ACCOUNT_LIST_LIMIT: Final[int] = 100

OPERATION_TEXT: Final[dict[str, dict[str, str]]] = {
    "deposit": {
        "title": "Depositar",
        "account_label": "Cuenta de destino",
        "button": "Depositar",
        "success": "Depósito realizado",
    },
    "withdraw": {
        "title": "Retirar",
        "account_label": "Cuenta de origen",
        "button": "Retirar",
        "success": "Retiro realizado",
    },
}


def _context(principal: Principal, **extra: object) -> dict[str, object]:
    """Build the template context shared by signed-in pages."""
    return {"principal": principal, **extra}


def _active_accounts(principal: Principal, session: Session) -> list[AccountRead]:
    """Return the active accounts the user can operate on."""
    page = AccountService(session, principal).list_accounts(
        limit=ACCOUNT_LIST_LIMIT,
        offset=0,
        owner_id=None,
        status=AccountStatus.ACTIVE,
        currency=None,
    )
    return page.items


def _redirect_with_message(path: str, message: str) -> RedirectResponse:
    """Redirect to [path] and show [message] once on the next page."""
    return RedirectResponse(f"{path}?{urlencode({'ok': message})}", status_code=303)


# ----------------------------------------------------------------- sign in


@router.get("/login")
def login_page(request: Request) -> Response:
    """Show the sign-in form."""
    if request.cookies.get(SESSION_COOKIE):
        return RedirectResponse("/", status_code=303)
    return _render_login(request)


def _render_login(
    request: Request,
    *,
    error: str | None = None,
    tenant_slug: str = "",
    email: str = "",
    status_code: int = 200,
) -> Response:
    """Render the login page with the values typed by the user."""
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": error, "tenant_slug": tenant_slug, "email": email},
        status_code=status_code,
    )


@router.post("/login")
def login_submit(
    request: Request,
    session: Session = Depends(get_session),
    tenant_slug: str = Form(default=""),
    email: str = Form(default=""),
    password: str = Form(default=""),
) -> Response:
    """Validate the form, sign the user in and store the token in a cookie."""
    try:
        token = AuthService(session).login(
            LoginRequest(tenant_slug=tenant_slug, email=email, password=password)
        )
    except ValidationError:
        return _render_login(
            request,
            error="Revisa los datos introducidos",
            tenant_slug=tenant_slug,
            email=email,
            status_code=422,
        )
    except AuthenticationError as exc:
        return _render_login(
            request,
            error=error_message(exc.code, exc.message),
            tenant_slug=tenant_slug,
            email=email,
            status_code=401,
        )

    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        token.access_token,
        max_age=token.expires_in,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )
    return response


@router.post("/logout")
def logout() -> RedirectResponse:
    """Forget the session cookie and return to the login page."""
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


# --------------------------------------------------------------- dashboard


@router.get("/")
def dashboard(
    request: Request,
    message: str | None = Query(default=None, alias="ok"),
    session: Session = Depends(get_session),
) -> Response:
    """Show the public landing to visitors and the accounts dashboard to signed-in clients."""
    try:
        principal = get_web_principal(request, session)
    except LoginRequiredError:
        return templates.TemplateResponse(request, "landing.html", {})
    accounts = AccountService(session, principal).list_accounts(
        limit=ACCOUNT_LIST_LIMIT,
        offset=0,
        owner_id=None,
        status=None,
        currency=None,
    )
    recent = TransactionService(session, principal).list_history(
        limit=5,
        offset=0,
        transaction_type=None,
        status=None,
        account_id=None,
        date_from=None,
        date_to=None,
    )
    own_numbers = {account.account_number for account in accounts.items}
    rows = [_row(tx, own_numbers) for tx in recent.items]
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        _context(principal, accounts=accounts.items, rows=rows, message=message),
    )


def _row(transaction: TransactionRead, own_numbers: set[str]) -> dict[str, object]:
    """Pair a movement with its direction, so the template can pick the sign."""
    return {
        "tx": transaction,
        "incoming": is_incoming(
            str(transaction.type),
            transaction.target_account_number,
            transaction.source_account_number,
            own_numbers,
        ),
    }


# -------------------------------------------------------------- operations


@router.get("/deposit")
def deposit_page(
    request: Request,
    principal: Principal = Depends(get_web_principal),
    session: Session = Depends(get_session),
) -> Response:
    """Show the deposit form with a fresh idempotency key."""
    return _render_operation(request, principal, session, "deposit", key=str(uuid.uuid4()), form={})


@router.get("/withdraw")
def withdraw_page(
    request: Request,
    principal: Principal = Depends(get_web_principal),
    session: Session = Depends(get_session),
) -> Response:
    """Show the withdrawal form with a fresh idempotency key."""
    return _render_operation(
        request, principal, session, "withdraw", key=str(uuid.uuid4()), form={}
    )


def _render_operation(
    request: Request,
    principal: Principal,
    session: Session,
    operation: str,
    *,
    key: str,
    form: dict[str, str],
    error: str | None = None,
    status_code: int = 200,
) -> Response:
    """Render the deposit or withdrawal form."""
    return templates.TemplateResponse(
        request,
        "operation.html",
        _context(
            principal,
            operation=operation,
            text=OPERATION_TEXT[operation],
            accounts=_active_accounts(principal, session),
            idempotency_key=key,
            form=form,
            error=error,
        ),
        status_code=status_code,
    )


@router.post("/deposit")
def deposit_submit(
    request: Request,
    principal: Principal = Depends(get_web_principal),
    session: Session = Depends(get_session),
    account_id: str = Form(default=""),
    amount: str = Form(default=""),
    description: str = Form(default=""),
    idempotency_key: str = Form(default=""),
) -> Response:
    """Credit the selected account once for the submitted key."""
    form = {"account_id": account_id, "amount": amount, "description": description}
    try:
        TransactionService(session, principal).deposit(
            uuid.UUID(account_id),
            DepositRequest(amount=amount, description=description or None),
            validate_idempotency_key(idempotency_key),
        )
    except ValidationError:
        error = "Introduce un importe válido, por ejemplo 25.50"
    except ValueError:
        error = "Selecciona una cuenta válida"
    except BankOSError as exc:
        error = error_message(exc.code, exc.message)
    else:
        return _redirect_with_message("/", OPERATION_TEXT["deposit"]["success"])
    return _render_operation(
        request,
        principal,
        session,
        "deposit",
        key=idempotency_key,
        form=form,
        error=error,
        status_code=422,
    )


@router.post("/withdraw")
def withdraw_submit(
    request: Request,
    principal: Principal = Depends(get_web_principal),
    session: Session = Depends(get_session),
    account_id: str = Form(default=""),
    amount: str = Form(default=""),
    description: str = Form(default=""),
    idempotency_key: str = Form(default=""),
) -> Response:
    """Debit the selected account once for the submitted key."""
    form = {"account_id": account_id, "amount": amount, "description": description}
    try:
        TransactionService(session, principal).withdraw(
            uuid.UUID(account_id),
            WithdrawalRequest(amount=amount, description=description or None),
            validate_idempotency_key(idempotency_key),
        )
    except ValidationError:
        error = "Introduce un importe válido, por ejemplo 25.50"
    except ValueError:
        error = "Selecciona una cuenta válida"
    except BankOSError as exc:
        error = error_message(exc.code, exc.message)
    else:
        return _redirect_with_message("/", OPERATION_TEXT["withdraw"]["success"])
    return _render_operation(
        request,
        principal,
        session,
        "withdraw",
        key=idempotency_key,
        form=form,
        error=error,
        status_code=422,
    )


# ---------------------------------------------------------------- transfers


@router.get("/transfer")
def transfer_page(
    request: Request,
    principal: Principal = Depends(get_web_principal),
    session: Session = Depends(get_session),
) -> Response:
    """Show the transfer form with a fresh idempotency key."""
    return _render_transfer(request, principal, session, key=str(uuid.uuid4()), form={})


def _render_transfer(
    request: Request,
    principal: Principal,
    session: Session,
    *,
    key: str,
    form: dict[str, str],
    quote: TransferQuote | None = None,
    error: str | None = None,
    status_code: int = 200,
) -> Response:
    """Render the transfer form, with the quote when one was requested."""
    return templates.TemplateResponse(
        request,
        "transfer.html",
        _context(
            principal,
            accounts=_active_accounts(principal, session),
            idempotency_key=key,
            form=form,
            quote=quote,
            error=error,
        ),
        status_code=status_code,
    )


@router.post("/transfer")
def transfer_submit(
    request: Request,
    principal: Principal = Depends(get_web_principal),
    session: Session = Depends(get_session),
    source_account_id: str = Form(default=""),
    target_account_number: str = Form(default=""),
    amount: str = Form(default=""),
    description: str = Form(default=""),
    idempotency_key: str = Form(default=""),
    action: str = Form(default="quote"),
) -> Response:
    """Show the cost of a transfer, or send it when the user confirms."""
    form = {
        "source_account_id": source_account_id,
        "target_account_number": target_account_number,
        "amount": amount,
        "description": description,
    }
    service = TransactionService(session, principal)
    try:
        source_id = uuid.UUID(source_account_id)
        if action == "confirm":
            service.transfer(
                TransferRequest(
                    source_account_id=source_id,
                    target_account_number=target_account_number,
                    amount=amount,
                    description=description or None,
                ),
                validate_idempotency_key(idempotency_key),
            )
            return _redirect_with_message("/", "Transferencia realizada")
        quote = service.quote(
            TransferPreviewRequest(
                source_account_id=source_id,
                target_account_number=target_account_number,
                amount=amount,
            )
        )
    except ValidationError:
        error = "Revisa la cuenta destino y el importe"
    except ValueError:
        error = "Selecciona una cuenta válida"
    except BankOSError as exc:
        error = error_message(exc.code, exc.message)
    else:
        return _render_transfer(
            request, principal, session, key=idempotency_key, form=form, quote=quote
        )
    return _render_transfer(
        request,
        principal,
        session,
        key=idempotency_key,
        form=form,
        error=error,
        status_code=422,
    )


# ------------------------------------------------------------- movements


@router.get("/transactions")
def transactions_page(
    request: Request,
    principal: Principal = Depends(get_web_principal),
    session: Session = Depends(get_session),
    offset: int = Query(default=0, ge=0),
    kind: str = Query(default="", alias="type"),
) -> Response:
    """Show the paginated movement history, optionally filtered by type."""
    transaction_type = _parse_transaction_type(kind)
    history = TransactionService(session, principal).list_history(
        limit=HISTORY_PAGE_SIZE,
        offset=offset,
        transaction_type=transaction_type,
        status=None,
        account_id=None,
        date_from=None,
        date_to=None,
    )
    own_numbers = {
        account.account_number
        for account in AccountService(session, principal)
        .list_accounts(
            limit=ACCOUNT_LIST_LIMIT,
            offset=0,
            owner_id=None,
            status=None,
            currency=None,
        )
        .items
    }
    return templates.TemplateResponse(
        request,
        "transactions.html",
        _context(
            principal,
            rows=[_row(tx, own_numbers) for tx in history.items],
            total=history.total,
            offset=offset,
            page_size=HISTORY_PAGE_SIZE,
            kind=kind,
        ),
    )


def _parse_transaction_type(kind: str) -> TransactionType | None:
    """Turn the filter value of the form into a movement type, or None for all."""
    if not kind:
        return None
    try:
        return TransactionType(kind)
    except ValueError:
        return None


# ---------------------------------------------------------------- profile


@router.get("/profile")
def profile_page(
    request: Request,
    principal: Principal = Depends(get_web_principal),
    session: Session = Depends(get_session),
) -> Response:
    """Show the signed-in user and the tenant they belong to."""
    tenant = TenantRepository(session).get(principal.tenant_id)
    return templates.TemplateResponse(
        request,
        "profile.html",
        _context(principal, tenant=tenant),
    )
