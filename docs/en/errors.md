# Errors

Every response uses a common JSON envelope. Successful and failed responses share `success`, `code`, `message` and `correlation_id`.

## Success envelope

```json
{
  "success": true,
  "code": "ACCOUNT_DETAIL",
  "message": "OK",
  "data": {},
  "correlation_id": "8f14e45f-ea0c-4b1f-9d5f-1c2a3b4c5d6e"
}
```

## Error envelope

```json
{
  "success": false,
  "code": "INSUFFICIENT_FUNDS",
  "message": "The source account does not have enough funds to cover the amount and fee",
  "details": {
    "balance": "0.00",
    "amount": "100.00",
    "fee": "2.00",
    "required": "102.00",
    "currency": "USD"
  },
  "correlation_id": "8f14e45f-ea0c-4b1f-9d5f-1c2a3b4c5d6e"
}
```

`details` can be `null`, an object or a list, depending on the error. It should not be used for business logic: the stable contract is `code`.

## HTTP status codes

| HTTP | Usage |
| --- | --- |
| `200` | Successful read or quote. |
| `201` | Resource created or financial operation completed. |
| `401` | Missing, invalid or expired token. |
| `403` | The authenticated user lacks the required role. |
| `404` | The resource does not exist or belongs to another tenant. |
| `409` | Conflict: duplicate slug, duplicate email or idempotency key in progress. |
| `422` | Body/parameter validation or business rule violation. |
| `429` | Rate limit exceeded. |
| `500` | Unexpected error. |

## Internal codes

| Code | HTTP | Meaning |
| --- | --- | --- |
| `UNAUTHENTICATED` | 401 | Invalid credentials or token. |
| `FORBIDDEN` | 403 | The role does not allow the action. |
| `NOT_FOUND` | 404 | Missing resource or resource from another tenant. |
| `CONFLICT` | 409 | Generic conflict. |
| `TENANT_SLUG_TAKEN` | 409 | The slug is already registered. |
| `USER_EMAIL_TAKEN` | 409 | The email already exists in the tenant. |
| `IDEMPOTENCY_IN_PROGRESS` | 409 | The key is being processed. |
| `VALIDATION_ERROR` | 422 | Invalid body or parameters. |
| `MISSING_IDEMPOTENCY_KEY` | 422 | The mandatory header is missing. |
| `INVALID_IDEMPOTENCY_KEY` | 422 | The header is not a UUID. |
| `BUSINESS_RULE_VIOLATION` | 422 | Generic business rule violation. |
| `INSUFFICIENT_FUNDS` | 422 | Insufficient balance. |
| `ACCOUNT_NOT_ACTIVE` | 422 | The account is not active. |
| `SAME_ACCOUNT_TRANSFER` | 422 | Source and target are the same. |
| `EXCHANGE_RATE_NOT_FOUND` | 422 | No rate exists for the pair. |
| `TRANSACTION_LIMIT_EXCEEDED` | 422 | Amount above the limit. |
| `INVALID_COMMISSION` | 422 | Negative commission or percentage above 100. |
| `INVALID_EXCHANGE_RATE` | 422 | Invalid rate or same-currency pair. |
| `DUPLICATE_EXCHANGE_RATE` | 422 | Repeated pair in the table. |
| `INVALID_ACCOUNT_OWNER` | 422 | The owner does not have the `client` role. |
| `INACTIVE_ACCOUNT_OWNER` | 422 | The owner is inactive. |
| `CANNOT_DEACTIVATE_SELF` | 422 | An administrator tries to deactivate themselves. |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests. |
| `HTTP_ERROR` | Varies | Starlette HTTP error, for example an unknown route. |
| `INTERNAL_ERROR` | 500 | Uncontrolled error. |

## Validation example

```json
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "message": "The request body or parameters are not valid",
  "details": [
    {
      "type": "greater_than",
      "loc": ["body", "amount"],
      "msg": "Input should be greater than 0",
      "input": "0"
    }
  ],
  "correlation_id": "8f14e45f-ea0c-4b1f-9d5f-1c2a3b4c5d6e"
}
```

## Tracing

The API accepts `X-Correlation-ID` on the request. If it is not sent, a UUID is generated. The value is returned in the response and the envelope, and it is propagated to logs and webhooks. If the header is longer than 64 characters, it is truncated.

```bash
curl http://127.0.0.1:8000/health \
  -H "X-Correlation-ID: demo-correlation-id"
```

## Rate limiting

When a limit is exceeded, the response includes `Retry-After`:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 12
```

```json
{
  "success": false,
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests, retry later",
  "details": {"retry_after_seconds": 12},
  "correlation_id": "8f14e45f-ea0c-4b1f-9d5f-1c2a3b4c5d6e"
}
```
