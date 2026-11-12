# Webhooks

Cada tenant puede configurar un endpoint HTTP que recibe una notificación cuando se completa una transferencia. La entrega es asíncrona y no bloquea la respuesta de la transferencia.

## Configurar el webhook

El endpoint se configura con `PATCH /api/v1/tenants/me`:

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/tenants/me \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://example.test/bankos/webhook"}'
```

La URL debe empezar por `http://` o `https://`. Para desactivar las notificaciones, envía `"webhook_url": null`.

## Evento

El único evento implementado es `transfer.received`. Se dispara cuando una transferencia se completa con éxito por primera vez. No se dispara para:

- depósitos;
- retiros;
- reintentos idempotentes que devuelven una respuesta almacenada;
- transferencias fallidas.

## Entrega

- Se ejecuta con `BackgroundTasks` de FastAPI después de responder al cliente.
- Se hace `POST` a la URL configurada con JSON.
- Cabeceras:
  - `Content-Type: application/json`
  - `X-Correlation-ID` con el identificador de la petición original.
- Timeout configurable con `WEBHOOK_TIMEOUT_SECONDS` por intento; por defecto, 5 segundos.
- Hasta 3 intentos.
- Espera de 0,5 s antes del segundo intento y 1 s antes del tercero.
- Si los tres intentos fallan, el evento se descarta y se registra un error en el log.

No hay firma HMAC, no hay cola persistente y no se guarda el estado de entrega. El webhook es de mejor esfuerzo.

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

Los importes se envían como cadenas con 2 decimales y la tasa como cadena con 6 decimales. `occurred_at` es la marca de creación de la transacción.

## Recomendaciones

- Usa HTTPS en producción.
- Valida el `X-Correlation-ID` para correlacionar logs.
- Responde rápido con `2xx`; el emisor no espera una lógica larga.
- Si necesitas garantía de entrega, implementa una cola persistente y verificación de firma fuera de este proyecto.
- Ajusta `WEBHOOK_TIMEOUT_SECONDS` si tu endpoint tarda más que el valor por defecto; el cambio se aplica al reiniciar la API.
