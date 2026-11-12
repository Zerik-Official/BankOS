# Accounts

Accounts belong to a tenant client and a currency. Every account has a unique number, a balance, a status and a creation timestamp.

## Create an account

Only an administrator can open accounts. The owner must be a user with the `client` role and must be active.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/accounts \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "3c2b1a09-8f7e-6d5c-4b3a-2f1e0d9c8b7a",
    "currency": "USD"
  }'
```

`201` response:

```json
{
  "success": true,
  "code": "ACCOUNT_CREATED",
  "message": "Account created",
  "data": {
    "id": "5d4c3b2a-1f0e-9d8c-7b6a-5f4e3d2c1b0a",
    "account_number": "731901614963",
    "owner_id": "3c2b1a09-8f7e-6d5c-4b3a-2f1e0d9c8b7a",
    "balance": "0.00",
    "currency": "USD",
    "status": "active",
    "created_at": "2026-11-12T10:05:00Z",
    "updated_at": "2026-11-12T10:05:00Z"
  },
  "correlation_id": "8f14e45f-ea0c-4b1f-9d5f-1c2a3b4c5d6e"
}
```

Rules:

- The account number is generated automatically with 12 digits and is unique across the platform.
- The currency must be a 3-letter code; it is normalized to uppercase.
- The initial balance is `0.00`.
- A user with the `administrator` role cannot own an account.
- An inactive owner is rejected with `422 INACTIVE_ACCOUNT_OWNER`.

## List accounts

```bash
curl "http://127.0.0.1:8000/api/v1/accounts?limit=20&offset=0&currency=USD" \
  -H "Authorization: Bearer $TOKEN"
```

Available filters:

| Parameter | Description |
| --- | --- |
| `limit` | Items per page, between 1 and 100. Defaults to 50. |
| `offset` | Items to skip. Defaults to 0. |
| `owner_id` | Filter by owner. Only administrators can use an owner other than their own. |
| `status` | `active`, `inactive` or `blocked`. |
| `currency` | 3-letter code. |

An administrator sees every account of the tenant. A client sees only their own, even if they send another `owner_id`.

Response:

```json
{
  "success": true,
  "code": "ACCOUNT_LIST",
  "message": "OK",
  "data": {
    "items": [
      {
        "id": "5d4c3b2a-1f0e-9d8c-7b6a-5f4e3d2c1b0a",
        "account_number": "731901614963",
        "owner_id": "3c2b1a09-8f7e-6d5c-4b3a-2f1e0d9c8b7a",
        "balance": "1000.00",
        "currency": "USD",
        "status": "active",
        "created_at": "2026-11-12T10:05:00Z",
        "updated_at": "2026-11-12T10:05:00Z"
      }
    ],
    "total": 1,
    "limit": 20,
    "offset": 0
  },
  "correlation_id": "8f14e45f-ea0c-4b1f-9d5f-1c2a3b4c5d6e"
}
```

## Read an account

```bash
curl http://127.0.0.1:8000/api/v1/accounts/$ACCOUNT_ID \
  -H "Authorization: Bearer $TOKEN"
```

A client can only read their own accounts. Any foreign account, even in the same tenant, responds `404 NOT_FOUND`.

## Change the account status

Deactivation is a soft delete: the row is preserved to keep the historical integrity. Only an administrator can change the status.

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/accounts/$ACCOUNT_ID/status \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "inactive"}'
```

States:

| State | Meaning |
| --- | --- |
| `active` | The account can receive deposits, withdrawals and transfers. |
| `inactive` | The account is deactivated and does not accept financial operations. |
| `blocked` | The account is blocked and does not accept financial operations. |

The response is the updated account with code `ACCOUNT_STATUS_UPDATED`. The change is recorded in the audit log as `account.status.updated`.

## Financial operations

An inactive or blocked account rejects deposits, withdrawals and transfers with `422 ACCOUNT_NOT_ACTIVE`. See [Operations](operations.md) and [Transfers and rates](transfers.md).
