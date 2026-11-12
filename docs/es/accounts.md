# Cuentas

Las cuentas pertenecen a un cliente del tenant y a una moneda. Cada cuenta tiene un número único, un saldo, un estado y una marca de creación.

## Crear una cuenta

Solo un administrador puede abrir cuentas. El titular debe ser un usuario con rol `client` y estar activo.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/accounts \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "3c2b1a09-8f7e-6d5c-4b3a-2f1e0d9c8b7a",
    "currency": "USD"
  }'
```

Respuesta `201`:

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

Reglas:

- El número de cuenta se genera automáticamente con 12 dígitos y es único en la plataforma.
- La moneda debe ser un código de 3 letras; se normaliza a mayúsculas.
- El saldo inicial es `0.00`.
- Un usuario con rol `administrator` no puede ser titular de una cuenta.
- Un titular inactivo es rechazado con `422 INACTIVE_ACCOUNT_OWNER`.

## Listar cuentas

```bash
curl "http://127.0.0.1:8000/api/v1/accounts?limit=20&offset=0&currency=USD" \
  -H "Authorization: Bearer $TOKEN"
```

Filtros disponibles:

| Parámetro | Descripción |
| --- | --- |
| `limit` | Elementos por página, entre 1 y 100. Por defecto 50. |
| `offset` | Elementos a omitir. Por defecto 0. |
| `owner_id` | Filtra por titular. Solo los administradores pueden usar un titular distinto del propio. |
| `status` | `active`, `inactive` o `blocked`. |
| `currency` | Código de 3 letras. |

Un administrador ve todas las cuentas del tenant. Un cliente ve solo las suyas, aunque envíe otro `owner_id`.

Respuesta:

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

## Leer una cuenta

```bash
curl http://127.0.0.1:8000/api/v1/accounts/$ACCOUNT_ID \
  -H "Authorization: Bearer $TOKEN"
```

Un cliente solo puede leer sus propias cuentas. Cualquier cuenta ajena, incluso del mismo tenant, responde `404 NOT_FOUND`.

## Cambiar el estado de una cuenta

La desactivación es un borrado lógico: la fila se conserva para mantener la integridad histórica. Solo un administrador puede cambiar el estado.

```bash
curl -X PATCH http://127.0.0.1:8000/api/v1/accounts/$ACCOUNT_ID/status \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "inactive"}'
```

Estados:

| Estado | Significado |
| --- | --- |
| `active` | La cuenta puede recibir depósitos, retiros y transferencias. |
| `inactive` | La cuenta está desactivada y no admite operaciones financieras. |
| `blocked` | La cuenta está bloqueada y no admite operaciones financieras. |

La respuesta es la cuenta actualizada con código `ACCOUNT_STATUS_UPDATED`. El cambio queda en auditoría como `account.status.updated`.

## Operaciones financieras

Una cuenta inactiva o bloqueada rechaza depósitos, retiros y transferencias con `422 ACCOUNT_NOT_ACTIVE`. Consulta [Operaciones](operations.md) y [Transferencias y tasas](transfers.md).
