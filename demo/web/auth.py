"""Cookie-based sign-in for the web frontend.

The access token from the login form is stored in an HTTP-only cookie, so
JavaScript on the page cannot read it.
"""

# Standard library
from typing import Final

# Third-party
from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

# Project imports
from app.api.dependencies import get_session
from app.core.errors import AuthenticationError
from app.core.principal import Principal
from app.core.security import decode_access_token
from app.services.auth import load_principal

SESSION_COOKIE: Final[str] = "bankos_session"


class LoginRequiredError(Exception):
    """Raised when a page needs a signed-in user and the cookie is missing or invalid."""


def get_web_principal(
    request: Request,
    session: Session = Depends(get_session),
) -> Principal:
    """Resolve the signed-in user from the session cookie."""
    token: str | None = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise LoginRequiredError()
    try:
        return load_principal(session, decode_access_token(token))
    except AuthenticationError as exc:
        raise LoginRequiredError() from exc


def redirect_to_login(request: Request, exc: LoginRequiredError) -> RedirectResponse:
    """Send the visitor to the login page and clear any stale cookie."""
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
