"""Password hashing and JWT helpers."""

# Standard library
import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

# Third-party
import jwt
from pydantic import BaseModel

# Project imports
from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.models.enums import UserRole

_PBKDF2_ITERATIONS = 260_000
_PBKDF2_PREFIX = "pbkdf2_sha256"


class TokenPayload(BaseModel):
    """Claims carried by an access token."""

    sub: str
    tenant_id: str
    role: UserRole
    email: str
    exp: int


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 and a random salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{_PBKDF2_PREFIX}${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Compare a plain password against a stored PBKDF2 hash."""
    try:
        prefix, iterations, salt_hex, digest_hex = stored_hash.split("$")
    except ValueError:
        return False
    if prefix != _PBKDF2_PREFIX:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(iterations),
    )
    return hmac.compare_digest(candidate.hex(), digest_hex)


def create_access_token(
    *,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    role: UserRole,
    email: str,
) -> tuple[str, int]:
    """Sign an access token and return it with its lifetime in seconds."""
    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.jwt_expires_minutes)
    payload: dict[str, object] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role.value,
        "email": email,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, settings.jwt_expires_minutes * 60


def decode_access_token(token: str) -> TokenPayload:
    """Validate and decode an access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "tenant_id", "role"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("The session token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("The session token is not valid") from exc

    if payload.get("type") != "access":
        raise AuthenticationError("The session token is not valid")

    try:
        return TokenPayload.model_validate(payload)
    except ValueError as exc:
        raise AuthenticationError("The session token is not valid") from exc
