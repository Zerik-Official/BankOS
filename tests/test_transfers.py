"""Transfer, commission, idempotency and multi-currency tests."""

# Standard library
import uuid
from datetime import timedelta
from typing import Any

# Third-party
from fastapi.testclient import TestClient
from httpx import Response

# Project imports
from app.core.clock import utc_now
from app.db.session import SessionLocal
from app.models.enums import IdempotencyStatus
from app.models.idempotency import IdempotencyRecord
from tests.helpers import (
    auth,
    balance,
    create_account,
    create_client_user,
    deposit,
    register_tenant,
)


def _transfer(
    client: TestClient,
    token: str,
    source_account_id: str,
    target_account_number: str,
    amount: str,
    key: str | None,
) -> Response:
    """Submit a transfer with an optional idempotency key."""
    headers = auth(token)
    if key is not None:
        headers["Idempotency-Key"] = key
    return client.post(
        "/api/v1/transfers",
        headers=headers,
        json={
            "source_account_id": source_account_id,
            "target_account_number": target_account_number,
            "amount": amount,
        },
    )


def _rates(client: TestClient, token: str, rates: list[dict[str, str]]) -> None:
    """Replace the exchange rate table of the current tenant."""
    response = client.put(
        "/api/v1/tenants/me/exchange-rates",
        headers=auth(token),
        json={"rates": rates},
    )
    assert response.status_code == 200, response.text


def _account_pair(
    client: TestClient, tenant: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create a client with a USD source account and a USD target account."""
    owner = create_client_user(client, tenant["token"], "carl@acme.test")
    source = create_account(client, tenant["token"], owner["id"], "USD")
    target = create_account(client, tenant["token"], owner["id"], "USD")
    return source, target


def test_transfer_charges_percentage_commission(client: TestClient) -> None:
    """A 2 percent commission is charged in the source currency."""
    acme = register_tenant(
        client,
        "acme",
        commission_type="percentage",
        commission_value="2",
    )
    source, target = _account_pair(client, acme)
    deposit(client, acme["token"], source["id"], "1000.00")

    response = _transfer(
        client,
        acme["token"],
        source["id"],
        target["account_number"],
        "100.00",
        str(uuid.uuid4()),
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["status"] == "success"
    assert data["amount"] == "100.00"
    assert data["fee"] == "2.00"
    assert data["exchange_rate"] == "1.000000"
    assert data["converted_amount"] == "100.00"
    assert data["currency"] == "USD"
    assert data["target_currency"] == "USD"
    assert balance(client, acme["token"], source["id"]) == "898.00"
    assert balance(client, acme["token"], target["id"]) == "100.00"


def test_transfer_requires_idempotency_key(client: TestClient) -> None:
    """A transfer without the Idempotency-Key header is rejected."""
    acme = register_tenant(client, "acme")
    source, target = _account_pair(client, acme)

    response = _transfer(
        client,
        acme["token"],
        source["id"],
        target["account_number"],
        "100.00",
        None,
    )

    assert response.status_code == 422
    assert response.json()["success"] is False
    assert response.json()["code"] == "MISSING_IDEMPOTENCY_KEY"


def test_transfer_rejects_invalid_idempotency_key(client: TestClient) -> None:
    """The Idempotency-Key header must be a UUID."""
    acme = register_tenant(client, "acme")
    source, target = _account_pair(client, acme)

    response = _transfer(
        client,
        acme["token"],
        source["id"],
        target["account_number"],
        "100.00",
        "not-a-uuid",
    )

    assert response.status_code == 422
    assert response.json()["success"] is False
    assert response.json()["code"] == "INVALID_IDEMPOTENCY_KEY"


def test_transfer_replay_returns_the_original_response(client: TestClient) -> None:
    """Reusing a key returns the stored response without moving funds again."""
    acme = register_tenant(
        client,
        "acme",
        commission_type="percentage",
        commission_value="2",
    )
    source, target = _account_pair(client, acme)
    deposit(client, acme["token"], source["id"], "1000.00")
    key = str(uuid.uuid4())

    first = _transfer(
        client,
        acme["token"],
        source["id"],
        target["account_number"],
        "100.00",
        key,
    )
    second = _transfer(
        client,
        acme["token"],
        source["id"],
        target["account_number"],
        "100.00",
        key,
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json() == first.json()
    assert second.json()["data"]["id"] == first.json()["data"]["id"]
    assert "X-Idempotent-Replayed" not in first.headers
    assert second.headers["X-Idempotent-Replayed"] == "true"
    assert balance(client, acme["token"], source["id"]) == "898.00"
    assert balance(client, acme["token"], target["id"]) == "100.00"


def test_transfer_in_progress_key_returns_conflict(client: TestClient) -> None:
    """A key already in progress produces 409 without executing the transfer."""
    acme = register_tenant(
        client,
        "acme",
        commission_type="percentage",
        commission_value="2",
    )
    source, target = _account_pair(client, acme)
    deposit(client, acme["token"], source["id"], "1000.00")
    key = str(uuid.uuid4())

    session = SessionLocal()
    try:
        session.add(
            IdempotencyRecord(
                tenant_id=uuid.UUID(acme["tenant"]["id"]),
                user_id=uuid.UUID(acme["admin"]["id"]),
                key=key,
                status=IdempotencyStatus.IN_PROGRESS,
                expires_at=utc_now() + timedelta(hours=1),
            )
        )
        session.commit()
    finally:
        session.close()

    response = _transfer(
        client,
        acme["token"],
        source["id"],
        target["account_number"],
        "100.00",
        key,
    )

    assert response.status_code == 409
    assert response.json()["code"] == "IDEMPOTENCY_IN_PROGRESS"
    assert balance(client, acme["token"], source["id"]) == "1000.00"
    assert balance(client, acme["token"], target["id"]) == "0.00"


def test_business_failure_releases_the_idempotency_key(client: TestClient) -> None:
    """Insufficient funds store an error transaction and allow a retry."""
    acme = register_tenant(
        client,
        "acme",
        commission_type="percentage",
        commission_value="2",
    )
    source, target = _account_pair(client, acme)
    key = str(uuid.uuid4())

    failed = _transfer(
        client,
        acme["token"],
        source["id"],
        target["account_number"],
        "100.00",
        key,
    )

    assert failed.status_code == 422, failed.text
    assert failed.json()["code"] == "INSUFFICIENT_FUNDS"

    history = client.get(
        "/api/v1/transactions",
        headers=auth(acme["token"]),
        params={"status": "error", "type": "transfer"},
    )
    assert history.status_code == 200, history.text
    errors = history.json()["data"]["items"]
    assert history.json()["data"]["total"] == 1
    assert errors[0]["status"] == "error"
    assert errors[0]["error_code"] == "INSUFFICIENT_FUNDS"
    assert errors[0]["idempotency_key"] == key
    assert balance(client, acme["token"], source["id"]) == "0.00"
    assert balance(client, acme["token"], target["id"]) == "0.00"

    deposit(client, acme["token"], source["id"], "200.00")

    retried = _transfer(
        client,
        acme["token"],
        source["id"],
        target["account_number"],
        "100.00",
        key,
    )

    assert retried.status_code == 201, retried.text
    assert retried.json()["data"]["status"] == "success"
    assert retried.json()["data"]["idempotency_key"] == key
    assert balance(client, acme["token"], source["id"]) == "98.00"
    assert balance(client, acme["token"], target["id"]) == "100.00"


def test_transfer_converts_currency_with_the_tenant_rate(client: TestClient) -> None:
    """A USD to EUR transfer applies the configured 0.9 rate."""
    acme = register_tenant(
        client,
        "acme",
        commission_type="percentage",
        commission_value="2",
    )
    _rates(
        client,
        acme["token"],
        [{"source_currency": "USD", "target_currency": "EUR", "rate": "0.900000"}],
    )
    owner = create_client_user(client, acme["token"], "carl@acme.test")
    source = create_account(client, acme["token"], owner["id"], "USD")
    target = create_account(client, acme["token"], owner["id"], "EUR")
    deposit(client, acme["token"], source["id"], "1000.00")

    response = _transfer(
        client,
        acme["token"],
        source["id"],
        target["account_number"],
        "100.00",
        str(uuid.uuid4()),
    )

    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["amount"] == "100.00"
    assert data["fee"] == "2.00"
    assert data["exchange_rate"] == "0.900000"
    assert data["converted_amount"] == "90.00"
    assert data["currency"] == "USD"
    assert data["target_currency"] == "EUR"
    assert balance(client, acme["token"], source["id"]) == "898.00"
    assert balance(client, acme["token"], target["id"]) == "90.00"


def test_transfer_quote_does_not_move_funds(client: TestClient) -> None:
    """The quote endpoint returns the cost breakdown without executing it."""
    acme = register_tenant(
        client,
        "acme",
        commission_type="percentage",
        commission_value="2",
    )
    _rates(
        client,
        acme["token"],
        [{"source_currency": "USD", "target_currency": "EUR", "rate": "0.900000"}],
    )
    owner = create_client_user(client, acme["token"], "carl@acme.test")
    source = create_account(client, acme["token"], owner["id"], "USD")
    target = create_account(client, acme["token"], owner["id"], "EUR")
    deposit(client, acme["token"], source["id"], "1000.00")

    response = client.post(
        "/api/v1/transfers/quote",
        headers=auth(acme["token"]),
        json={
            "source_account_id": source["id"],
            "target_account_number": target["account_number"],
            "amount": "100.00",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["amount"] == "100.00"
    assert data["fee"] == "2.00"
    assert data["total_debit"] == "102.00"
    assert data["exchange_rate"] == "0.900000"
    assert data["converted_amount"] == "90.00"
    assert data["source_currency"] == "USD"
    assert data["target_currency"] == "EUR"
    assert balance(client, acme["token"], source["id"]) == "1000.00"
    assert balance(client, acme["token"], target["id"]) == "0.00"
