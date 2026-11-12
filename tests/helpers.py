"""Helpers that build API fixtures through the public endpoints."""

# Standard library
import uuid
from typing import Any

# Third-party
from fastapi.testclient import TestClient

DEFAULT_PASSWORD = "Password123"


def register_tenant(
    client: TestClient,
    slug: str,
    *,
    base_currency: str = "USD",
    commission_type: str = "percentage",
    commission_value: str = "0",
    email: str | None = None,
) -> dict[str, Any]:
    """Register a tenant with its administrator and return the session."""
    admin_email = email or f"admin@{slug}.test"
    response = client.post(
        "/api/v1/tenants",
        json={
            "name": f"Bank {slug}",
            "slug": slug,
            "admin_email": admin_email,
            "admin_full_name": "Ada Admin",
            "admin_password": DEFAULT_PASSWORD,
            "base_currency": base_currency,
            "commission_type": commission_type,
            "commission_value": commission_value,
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()["data"]
    token = login(client, slug, admin_email)
    return {"tenant": payload["tenant"], "admin": payload["admin"], "token": token}


def login(client: TestClient, slug: str, email: str, password: str = DEFAULT_PASSWORD) -> str:
    """Log in and return the bearer token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": slug, "email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["access_token"]


def auth(token: str) -> dict[str, str]:
    """Return the authorization headers for a token."""
    return {"Authorization": f"Bearer {token}"}


def create_client_user(client: TestClient, admin_token: str, email: str) -> dict[str, Any]:
    """Create an active client inside the tenant of the administrator."""
    response = client.post(
        "/api/v1/users",
        headers=auth(admin_token),
        json={"email": email, "full_name": "Carl Client", "password": DEFAULT_PASSWORD},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def create_account(client: TestClient, token: str, owner_id: str, currency: str) -> dict[str, Any]:
    """Open an account for a client."""
    response = client.post(
        "/api/v1/accounts",
        headers=auth(token),
        json={"owner_id": owner_id, "currency": currency},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def deposit(
    client: TestClient,
    token: str,
    account_id: str,
    amount: str,
    key: str | None = None,
) -> Any:
    """Deposit money using an idempotency key (generated when omitted)."""
    return client.post(
        f"/api/v1/accounts/{account_id}/deposits",
        headers={**auth(token), "Idempotency-Key": key or str(uuid.uuid4())},
        json={"amount": amount},
    )


def balance(client: TestClient, token: str, account_id: str) -> str:
    """Return the current balance of an account as a string."""
    response = client.get(f"/api/v1/accounts/{account_id}", headers=auth(token))
    assert response.status_code == 200, response.text
    return response.json()["data"]["balance"]
