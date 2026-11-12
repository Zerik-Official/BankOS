"""Tenant isolation and role visibility tests."""

# Third-party
from fastapi.testclient import TestClient

# Project imports
from tests.helpers import (
    auth,
    create_account,
    create_client_user,
    deposit,
    login,
    register_tenant,
)


def test_tenant_cannot_read_a_foreign_account(client: TestClient) -> None:
    """An account of another tenant is reported as not found."""
    acme = register_tenant(client, "acme")
    globex = register_tenant(client, "globex")

    owner = create_client_user(client, acme["token"], "carl@acme.test")
    account = create_account(client, acme["token"], owner["id"], "USD")

    response = client.get(f"/api/v1/accounts/{account['id']}", headers=auth(globex["token"]))

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_tenant_cannot_deposit_into_a_foreign_account(client: TestClient) -> None:
    """Even a valid administrator cannot operate across tenants."""
    acme = register_tenant(client, "acme")
    globex = register_tenant(client, "globex")

    owner = create_client_user(client, acme["token"], "carl@acme.test")
    account = create_account(client, acme["token"], owner["id"], "USD")

    response = deposit(client, globex["token"], account["id"], "100.00")

    assert response.status_code == 404


def test_client_only_sees_own_accounts(client: TestClient) -> None:
    """Clients are restricted to the accounts they own."""
    acme = register_tenant(client, "acme")
    carl = create_client_user(client, acme["token"], "carl@acme.test")
    dina = create_client_user(client, acme["token"], "dina@acme.test")
    carl_account = create_account(client, acme["token"], carl["id"], "USD")
    create_account(client, acme["token"], dina["id"], "USD")

    carl_token = login(client, "acme", "carl@acme.test")
    listing = client.get("/api/v1/accounts", headers=auth(carl_token))

    assert listing.status_code == 200
    assert listing.json()["data"]["total"] == 1
    assert listing.json()["data"]["items"][0]["id"] == carl_account["id"]

    foreign = client.get(f"/api/v1/accounts/{carl_account['id']}", headers=auth(carl_token))
    assert foreign.status_code == 200

    other = create_account(client, acme["token"], dina["id"], "EUR")
    hidden = client.get(f"/api/v1/accounts/{other['id']}", headers=auth(carl_token))
    assert hidden.status_code == 404


def test_client_cannot_list_users(client: TestClient) -> None:
    """User administration is reserved to administrators."""
    acme = register_tenant(client, "acme")
    create_client_user(client, acme["token"], "carl@acme.test")
    carl_token = login(client, "acme", "carl@acme.test")

    response = client.get("/api/v1/users", headers=auth(carl_token))

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_audit_logs_are_tenant_scoped(client: TestClient) -> None:
    """Audit entries never leak between tenants."""
    acme = register_tenant(client, "acme")
    globex = register_tenant(client, "globex")
    create_client_user(client, acme["token"], "carl@acme.test")

    acme_logs = client.get("/api/v1/audit-logs", headers=auth(acme["token"]))
    globex_logs = client.get("/api/v1/audit-logs", headers=auth(globex["token"]))

    assert acme_logs.status_code == 200
    assert globex_logs.status_code == 200
    assert acme_logs.json()["data"]["total"] == 3
    assert globex_logs.json()["data"]["total"] == 2
    assert {entry["action"] for entry in acme_logs.json()["data"]["items"]} == {
        "tenant.created",
        "user.created",
    }
    assert {entry["action"] for entry in globex_logs.json()["data"]["items"]} == {
        "tenant.created",
        "user.created",
    }
