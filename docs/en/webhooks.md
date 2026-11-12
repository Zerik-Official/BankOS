# Webhooks

Every tenant can configure an HTTP endpoint that receives a notification when a transfer is completed. Delivery is asynchronous and does not block the transfer response.

## Configure the webhook

The endpoint is configured with `PATCH /api/v1/tenants/me`:

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/tenants/me \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://example.test/bankos/webhook"}'
```

The URL must start with `http://` or `https://`. To disable notifications, send `"webhook_url": null`.

## Event

The only implemented event is `transfer.received`. It fires when a transfer completes successfully for the first time. It does not fire for:

- deposits;
- withdrawals;
- idempotent retries that return a stored response;
- failed transfers.

## Delivery

- It runs with FastAPI `BackgroundTasks` after responding to the client.
- It sends a `POST` to the configured URL with JSON.
- Headers:
  - `Content-Type: application/json`
  - `X-Correlation-ID` with the identifier of the original request.
- Configurable timeout per attempt with `WEBHOOK_TIMEOUT_SECONDS`; 5 seconds by default.
- Up to 3 attempts.
- A 0.5 s wait before the second attempt and 1 s before the third.
- If all three attempts fail, the event is discarded and an error is logged.

There is no HMAC signature, no persistent queue and no delivery state. The webhook is best effort.

## Payload

```json
{
  "event": "transfer.received",
  "tenant_id": "4f3f0f0e-6d1a-4b5e-9f4e-2f5a1c7d8e90",
  "tenant_slug": "acme",
  "transaction_id": "1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "source_account_number": "731901614963",
  "target_account_number": "838433939096",
  "amount": "100.00",
  "currency": "USD",
  "converted_amount": "90.00",
  "target_currency": "EUR",
  "exchange_rate": "0.900000",
  "fee": "2.00",
  "description": "Monthly transfer",
  "occurred_at": "2026-11-12T10:20:00"
}
```

Amounts are sent as strings with 2 decimals and the rate as a string with 6 decimals. `occurred_at` is the transaction creation timestamp.

## Recommendations

- Use HTTPS in production.
- Read `X-Correlation-ID` to correlate logs.
- Respond quickly with `2xx`; the sender does not wait for long logic.
- If you need delivery guarantees, implement a persistent queue and signature verification outside this project.
- Adjust `WEBHOOK_TIMEOUT_SECONDS` if your endpoint takes longer than the default; the change applies after restarting the API.
