# Errores

Todas las respuestas usan un sobre JSON común. Las respuestas exitosas y las fallidas comparten `success`, `code`, `message` y `correlation_id`.

## Sobre de éxito

```json
{
  "success": true,
  "code": "ACCOUNT_DETAIL",
  "message": "OK",
  "data": {},
  "correlation_id": "8f14e45f-ea0c-4b1f-9d5f-1c2a3b4c5d6e"
}
```

## Sobre de error

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

`details` puede ser `null`, un objeto o una lista, según el error. No debe usarse para lógica de negocio: el contrato estable es `code`.

## Códigos HTTP

| HTTP | Uso |
| --- | --- |
| `200` | Lectura o cotización correcta. |
| `201` | Recurso creado o operación financiera completada. |
| `401` | Falta el token, es inválido o expiró. |
| `403` | El usuario autenticado no tiene el rol necesario. |
| `404` | El recurso no existe o pertenece a otro tenant. |
| `409` | Conflicto: slug duplicado, correo duplicado o clave de idempotencia en curso. |
| `422` | Validación de cuerpo/parámetros o regla de negocio incumplida. |
| `429` | Límite de peticiones superado. |
| `500` | Error inesperado. |

## Códigos internos

| Código | HTTP | Significado |
| --- | --- | --- |
| `UNAUTHENTICATED` | 401 | Credenciales o token inválidos. |
| `FORBIDDEN` | 403 | El rol no permite la acción. |
| `NOT_FOUND` | 404 | Recurso inexistente o de otro tenant. |
| `CONFLICT` | 409 | Conflicto genérico. |
| `TENANT_SLUG_TAKEN` | 409 | El slug ya está registrado. |
| `USER_EMAIL_TAKEN` | 409 | El correo ya existe en el tenant. |
| `IDEMPOTENCY_IN_PROGRESS` | 409 | La clave se está procesando. |
| `VALIDATION_ERROR` | 422 | Cuerpo o parámetros inválidos. |
| `MISSING_IDEMPOTENCY_KEY` | 422 | Falta la cabecera obligatoria. |
| `INVALID_IDEMPOTENCY_KEY` | 422 | La cabecera no es un UUID. |
| `BUSINESS_RULE_VIOLATION` | 422 | Regla de negocio genérica. |
| `INSUFFICIENT_FUNDS` | 422 | Saldo insuficiente. |
| `ACCOUNT_NOT_ACTIVE` | 422 | La cuenta no está activa. |
| `SAME_ACCOUNT_TRANSFER` | 422 | Origen y destino coinciden. |
| `EXCHANGE_RATE_NOT_FOUND` | 422 | No hay tasa para el par. |
| `TRANSACTION_LIMIT_EXCEEDED` | 422 | Importe por encima del límite. |
| `INVALID_COMMISSION` | 422 | Comisión negativa o porcentaje mayor que 100. |
| `INVALID_EXCHANGE_RATE` | 422 | Tasa inválida o par de la misma moneda. |
| `DUPLICATE_EXCHANGE_RATE` | 422 | Par repetido en la tabla. |
| `INVALID_ACCOUNT_OWNER` | 422 | El titular no tiene rol `client`. |
| `INACTIVE_ACCOUNT_OWNER` | 422 | El titular está inactivo. |
| `CANNOT_DEACTIVATE_SELF` | 422 | Un administrador intenta desactivarse. |
| `RATE_LIMIT_EXCEEDED` | 429 | Demasiadas peticiones. |
| `HTTP_ERROR` | Variable | Error HTTP de Starlette, por ejemplo una ruta inexistente. |
| `INTERNAL_ERROR` | 500 | Error no controlado. |

## Ejemplo de validación

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

## Trazabilidad

La API acepta `X-Correlation-ID` en la petición. Si no se envía, genera un UUID. El valor se devuelve en la respuesta y en el sobre, y se propaga a los logs y a los webhooks. Si la cabecera supera 64 caracteres, se trunca.

```bash
curl http://127.0.0.1:8000/health \
  -H "X-Correlation-ID: demo-correlation-id"
```

## Límite de peticiones

Cuando se supera un límite, la respuesta incluye `Retry-After`:

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
