"""Tests for the server-rendered web frontend."""

# Standard library
import re
import uuid
from typing import Any

# Third-party
from fastapi.testclient import TestClient

# Project imports
from tests.helpers import (
    DEFAULT_PASSWORD,
    balance,
    create_account,
    create_client_user,
    deposit,
    register_tenant,
)

KEY_PATTERN = re.compile(r'name="idempotency_key" value="([0-9a-f-]{36})"')
CLIENT_EMAIL = "alice@acme.test"
OTHER_EMAIL = "bob@acme.test"


def _seed_bank(client: TestClient) -> dict[str, Any]:
    """Create a tenant with two clients, each with a USD account and 100.00 of balance."""
    session = register_tenant(client, "acme")
    admin_token: str = session["token"]
    alice = create_client_user(client, admin_token, CLIENT_EMAIL)
    bob = create_client_user(client, admin_token, OTHER_EMAIL)
    alice_account = create_account(client, admin_token, alice["id"], "USD")
    bob_account = create_account(client, admin_token, bob["id"], "USD")
    deposit(client, admin_token, alice_account["id"], "100.00")
    return {
        "admin_token": admin_token,
        "alice_account": alice_account,
        "bob_account": bob_account,
    }


def _sign_in(client: TestClient, email: str = CLIENT_EMAIL) -> None:
    """Sign in through the login form, which stores the session cookie."""
    response = client.post(
        "/login",
        data={"tenant_slug": "acme", "email": email, "password": DEFAULT_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text
    assert response.headers["location"] == "/"


def _form_key(client: TestClient, path: str) -> str:
    """Load a form page and return the idempotency key it carries."""
    response = client.get(path)
    assert response.status_code == 200, response.text
    match = KEY_PATTERN.search(response.text)
    assert match is not None
    return match.group(1)


def test_root_shows_the_landing_without_session(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 200
    assert "Tu banco, siempre contigo" in response.text
    assert 'href="/login"' in response.text


def test_login_page_shows_the_form(client: TestClient) -> None:
    response = client.get("/login")

    assert response.status_code == 200
    assert 'name="password"' in response.text


def test_wrong_password_shows_a_spanish_message(client: TestClient) -> None:
    _seed_bank(client)

    response = client.post(
        "/login",
        data={"tenant_slug": "acme", "email": CLIENT_EMAIL, "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert "Entidad, correo o contraseña incorrectos" in response.text


def test_login_sets_an_http_only_cookie_and_shows_the_dashboard(client: TestClient) -> None:
    _seed_bank(client)

    login = client.post(
        "/login",
        data={"tenant_slug": "acme", "email": CLIENT_EMAIL, "password": DEFAULT_PASSWORD},
        follow_redirects=False,
    )
    dashboard = client.get("/")

    assert "bankos_session=" in login.headers["set-cookie"]
    assert "httponly" in login.headers["set-cookie"].lower()
    assert dashboard.status_code == 200
    assert "Hola, Carl Client" in dashboard.text
    assert "100.00 USD" in dashboard.text


def test_dashboard_does_not_show_another_clients_account(client: TestClient) -> None:
    seeded = _seed_bank(client)
    _sign_in(client)

    response = client.get("/")

    assert seeded["alice_account"]["account_number"] not in response.text
    assert seeded["alice_account"]["account_number"][-4:] in response.text
    assert seeded["bob_account"]["account_number"] not in response.text


def test_deposit_form_credits_the_account(client: TestClient) -> None:
    seeded = _seed_bank(client)
    _sign_in(client)
    key = _form_key(client, "/deposit")

    response = client.post(
        "/deposit",
        data={
            "account_id": seeded["alice_account"]["id"],
            "amount": "25.50",
            "description": "Ahorro",
            "idempotency_key": key,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/?ok=")
    assert balance(client, seeded["admin_token"], seeded["alice_account"]["id"]) == "125.50"


def test_repeating_a_deposit_with_the_same_key_credits_once(client: TestClient) -> None:
    seeded = _seed_bank(client)
    _sign_in(client)
    key = _form_key(client, "/deposit")
    data = {
        "account_id": seeded["alice_account"]["id"],
        "amount": "10.00",
        "idempotency_key": key,
    }

    client.post("/deposit", data=data, follow_redirects=False)
    client.post("/deposit", data=data, follow_redirects=False)

    assert balance(client, seeded["admin_token"], seeded["alice_account"]["id"]) == "110.00"


def test_invalid_amount_is_rejected_with_a_message(client: TestClient) -> None:
    seeded = _seed_bank(client)
    _sign_in(client)

    response = client.post(
        "/deposit",
        data={
            "account_id": seeded["alice_account"]["id"],
            "amount": "abc",
            "idempotency_key": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 422
    assert "Introduce un importe válido" in response.text


def test_withdrawal_without_funds_shows_a_spanish_message(client: TestClient) -> None:
    seeded = _seed_bank(client)
    _sign_in(client)

    response = client.post(
        "/withdraw",
        data={
            "account_id": seeded["alice_account"]["id"],
            "amount": "999.00",
            "idempotency_key": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 422
    assert "No tienes fondos suficientes" in response.text
    assert balance(client, seeded["admin_token"], seeded["alice_account"]["id"]) == "100.00"


def test_transfer_quote_then_confirm_moves_the_money(client: TestClient) -> None:
    seeded = _seed_bank(client)
    _sign_in(client)
    key = _form_key(client, "/transfer")
    form = {
        "source_account_id": seeded["alice_account"]["id"],
        "target_account_number": seeded["bob_account"]["account_number"],
        "amount": "10.00",
        "idempotency_key": key,
    }

    quote = client.post("/transfer", data={**form, "action": "quote"})
    confirm = client.post("/transfer", data={**form, "action": "confirm"}, follow_redirects=False)

    assert quote.status_code == 200
    assert "Tipo de cambio" in quote.text
    assert confirm.status_code == 303
    assert balance(client, seeded["admin_token"], seeded["alice_account"]["id"]) == "90.00"
    assert balance(client, seeded["admin_token"], seeded["bob_account"]["id"]) == "10.00"


def test_transactions_page_lists_the_history(client: TestClient) -> None:
    _seed_bank(client)
    _sign_in(client)

    response = client.get("/transactions")

    assert response.status_code == 200
    assert "Depósito" in response.text


def test_profile_shows_the_user_and_tenant(client: TestClient) -> None:
    _seed_bank(client)
    _sign_in(client)

    response = client.get("/profile")

    assert response.status_code == 200
    assert CLIENT_EMAIL in response.text
    assert "Cliente" in response.text


def test_logout_clears_the_session(client: TestClient) -> None:
    _seed_bank(client)
    _sign_in(client)

    logout = client.post("/logout", follow_redirects=False)
    dashboard = client.get("/", follow_redirects=False)

    assert logout.status_code == 303
    assert logout.headers["location"] == "/login"
    assert dashboard.status_code == 200
    assert "Tu banco, siempre contigo" in dashboard.text
    assert "Hola," not in dashboard.text


def test_forged_cookie_is_treated_as_signed_out(client: TestClient) -> None:
    _seed_bank(client)
    client.cookies.set("bankos_session", "not-a-real-token")

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 200
    assert "Tu banco, siempre contigo" in response.text
