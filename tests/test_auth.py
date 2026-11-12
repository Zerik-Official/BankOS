"""Authentication and tenant registration tests."""

# Third-party
from fastapi.testclient import TestClient

# Project imports
from tests.helpers import auth, login, register_tenant


def test_register_tenant_and_login(client: TestClient) -> None:
    """A tenant is created together with its administrator, who can log in."""
    session = register_tenant(client, "acme")

    assert session["tenant"]["slug"] == "acme"
    assert session["admin"]["role"] == "administrator"
    assert "password" not in session["admin"]

    profile = client.get("/api/v1/auth/me", headers=auth(session["token"]))
    assert profile.status_code == 200
    assert profile.json()["data"]["email"] == "admin@acme.test"
    assert profile.json()["correlation_id"]


def test_login_rejects_wrong_password(client: TestClient) -> None:
    """Bad credentials produce a 401 with the standard error envelope."""
    register_tenant(client, "acme")

    response = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "acme",
            "email": "admin@acme.test",
            "password": "WrongPassword1",
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHENTICATED"
    assert response.json()["success"] is False


def test_duplicate_slug_is_rejected(client: TestClient) -> None:
    """Two tenants cannot share a slug."""
    register_tenant(client, "acme")

    response = client.post(
        "/api/v1/tenants",
        json={
            "name": "Other Bank",
            "slug": "acme",
            "admin_email": "other@acme.test",
            "admin_full_name": "Other Admin",
            "admin_password": "Password123",
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "TENANT_SLUG_TAKEN"


def test_login_is_scoped_to_the_tenant(client: TestClient) -> None:
    """The same email in another tenant is a different user."""
    register_tenant(client, "acme")
    register_tenant(client, "globex")

    token = login(client, "globex", "admin@globex.test")
    profile = client.get("/api/v1/auth/me", headers=auth(token))

    assert profile.status_code == 200
    assert profile.json()["data"]["email"] == "admin@globex.test"


def test_protected_endpoints_require_a_token(client: TestClient) -> None:
    """Missing credentials are rejected before reaching the service."""
    response = client.get("/api/v1/accounts")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
