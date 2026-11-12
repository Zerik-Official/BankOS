# Audit

BankOS keeps a read-only audit log for relevant administrative actions. Every entry stores the actor, the action, the affected entity, the previous state and the new state.

## Read the audit log

```bash
curl "http://127.0.0.1:8000/api/v1/audit-logs?limit=20&offset=0" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Only an administrator can read the audit log. Results are scoped to the token tenant and ordered from newest to oldest.

`200` response:

```json
{
  "success": true,
  "code": "AUDIT_LOG_LIST",
  "message": "OK",
  "data": {
    "items": [
      {
        "id": "6f5e4d3c-2b1a-0f9e-8d7c-6b5a4f3e2d1c",
        "actor_user_id": "9a7b6c5d-4e3f-2a1b-0c9d-8e7f6a5b4c3d",
        "action": "account.created",
        "entity_type": "account",
        "entity_id": "5d4c3b2a-1f0e-9d8c-7b6a-5f4e3d2c1b0a",
        "previous_state": null,
        "new_state": {
          "account_number": "731901614963",
          "owner_id": "3c2b1a09-8f7e-6d5c-4b3a-2f1e0d9c8b7a",
          "currency": "USD",
          "status": "active"
        },
        "correlation_id": "8f14e45f-ea0c-4b1f-9d5f-1c2a3b4c5d6e",
        "created_at": "2026-11-12T10:05:00Z"
      }
    ],
    "total": 1,
    "limit": 20,
    "offset": 0
  },
  "correlation_id": "8f14e45f-ea0c-4b1f-9d5f-1c2a3b4c5d6e"
}
```

## Fields

| Field | Description |
| --- | --- |
| `id` | Entry UUID. |
| `actor_user_id` | User who performed the action; it can be `null` if the user was deleted. |
| `action` | Stable action name. |
| `entity_type` | Type of the affected entity. |
| `entity_id` | Identifier of the affected entity. |
| `previous_state` | Previous state, or `null` when not applicable. |
| `new_state` | New state, or `null` when not applicable. |
| `correlation_id` | Trace identifier of the request that produced the entry. |
| `created_at` | UTC date and time. |

## Recorded actions

| Action | Source |
| --- | --- |
| `tenant.created` | Public tenant registration. |
| `user.created` | Creation of the initial administrator and new users. |
| `user.updated` | Change of a user name or state. |
| `tenant.config.updated` | Tenant configuration change. |
| `tenant.exchange_rates.replaced` | Exchange rate table replacement. |
| `account.created` | Account opening. |
| `account.status.updated` | Account status change. |

Financial operations are not written to the administrative audit log: they are stored in the transactions table and read with `GET /api/v1/transactions`. This separation avoids duplicating the financial history.

## Immutability

- There are no endpoints to modify or delete audit entries.
- The table is append-only from the API.
- Entries are always filtered by `tenant_id`.
- Configuration changes store `previous_state` and `new_state` so the difference can be reconstructed.

Immutability is logical and enforced by the application: direct write access to SQLite could modify the table. A cryptographic or database-level guarantee would require sealing or external permissions, which are outside this project.
