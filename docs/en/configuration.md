# Configuration

BankOS is configured at two levels: process environment variables and settings persisted per tenant.

## Environment variables

Copy `.env.example` to `.env` and adjust the values. The application reads the `.env` file on startup.

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `BankOS API` | Visible API name and OpenAPI metadata. |
| `ENVIRONMENT` | `local` | Execution environment. It is written to the startup logs. |
| `DOCS_ENABLED` | `true` | Exposes `/docs`, `/redoc` and `/openapi.json`. It can be disabled in production. |
| `LOG_LEVEL` | `INFO` | Minimum logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `DATABASE_URL` | `sqlite:///./data/bankos.db` | SQLAlchemy URL. Docker uses `sqlite:////app/data/bankos.db`. |
| `JWT_SECRET_KEY` | Insecure development value | HMAC key used to sign and verify JWTs. **It must be changed**. |
| `JWT_ALGORITHM` | `HS256` | Token signing algorithm. |
| `JWT_EXPIRES_MINUTES` | `60` | Access token lifetime in minutes. |
| `CORS_ORIGINS` | `http://localhost:8000,http://localhost:5173` | Allowed origins, separated by commas. |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `10` | Login attempts allowed per IP per minute. |
| `RATE_LIMIT_FINANCIAL_PER_MINUTE` | `30` | Financial operations allowed per user and tenant per minute. |
| `RATE_LIMIT_IP_PER_MINUTE` | `120` | Global per-IP limit per minute for `/api/v1` routes. |
| `WEBHOOK_TIMEOUT_SECONDS` | `5` | Timeout in seconds for each webhook delivery attempt. It must be greater than 0. It is read when the application is imported; a change requires a process restart. |

Rate limits are stored in memory and read when the application is imported. A change requires a process restart.

## Example `.env`

```dotenv
APP_NAME=BankOS API
ENVIRONMENT=local
DOCS_ENABLED=true
LOG_LEVEL=INFO

DATABASE_URL=sqlite:///./data/bankos.db

JWT_SECRET_KEY=replace-this-with-a-long-random-value
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=60

CORS_ORIGINS=http://localhost:8000,http://localhost:5173
RATE_LIMIT_AUTH_PER_MINUTE=10
RATE_LIMIT_FINANCIAL_PER_MINUTE=30
RATE_LIMIT_IP_PER_MINUTE=120
WEBHOOK_TIMEOUT_SECONDS=5
```

## Per-tenant configuration

Every tenant stores its own configuration. It is read with `GET /api/v1/tenants/me` and changed with `PATCH /api/v1/tenants/me`. Only an administrator can change it.

| Field | Type | Description |
| --- | --- | --- |
| `name` | Text | Institution name. |
| `slug` | Text | Unique identifier, immutable after registration. |
| `base_currency` | 3-letter currency | Main currency declared by the tenant. It does not restrict account currencies. |
| `max_transaction_amount` | Money | Maximum amount per operation, expressed in the operation currency. Defaults to `1000000.00`. |
| `commission_type` | `percentage` or `fixed` | How outgoing transfer commissions are calculated. |
| `commission_value` | Decimal | Percentage (for example `2` means 2 %) or fixed amount in the source currency. |
| `webhook_url` | HTTP/HTTPS URL or `null` | Endpoint that receives the `transfer.received` event. |
| `is_active` | Boolean | Allows disabling the tenant. An inactive tenant cannot authenticate users. |

### Update the configuration

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/tenants/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "commission_type": "percentage",
    "commission_value": "2",
    "max_transaction_amount": "50000.00",
    "webhook_url": "https://example.test/bankos/webhook"
  }'
```

Response:

```json
{
  "success": true,
  "code": "TENANT_UPDATED",
  "message": "Tenant updated",
  "data": {
    "id": "4f3f0f0e-6d1a-4b5e-9f4e-2f5a1c7d8e90",
    "name": "Acme Demo Bank",
    "slug": "acme",
    "base_currency": "USD",
    "max_transaction_amount": "50000.00",
    "commission_type": "percentage",
    "commission_value": "2.000000",
    "webhook_url": "https://example.test/bankos/webhook",
    "is_active": true,
    "created_at": "2026-11-12T10:00:00Z"
  },
  "correlation_id": "8f14e45f-ea0c-4b1f-9d5f-1c2a3b4c5d6e"
}
```

Only the fields that are sent are changed. To clear the webhook, send `"webhook_url": null`.

### Exchange rates

The rate table is static and belongs to the tenant. It is read with `GET /api/v1/tenants/me/exchange-rates` and fully replaced with `PUT /api/v1/tenants/me/exchange-rates`.

```bash
curl -X PUT http://127.0.0.1:8000/api/v1/tenants/me/exchange-rates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rates": [
      {"source_currency": "USD", "target_currency": "EUR", "rate": "0.900000"},
      {"source_currency": "EUR", "target_currency": "USD", "rate": "1.100000"}
    ]
  }'
```

Rules:

- Every `source_currency` + `target_currency` pair must be unique.
- A currency cannot be converted to itself.
- The rate must be positive and accepts up to 6 decimals.
- The table accepts up to 100 pairs.
- The full replacement is recorded in the audit log.

## Database

SQLite is the target database both locally and in Docker. The schema is created with `Base.metadata.create_all` when the application starts. Alembic is not used. If the schema changes on an existing database, the migration must be applied manually or the database must be recreated.

The local database lives in `data/bankos.db`. In Docker it lives in `/app/data/bankos.db`, inside the `bankos-data` volume.
