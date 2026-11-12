# Auditoría

BankOS mantiene un registro de auditoría de solo lectura para las acciones administrativas relevantes. Cada entrada guarda el actor, la acción, la entidad afectada, el estado anterior y el estado nuevo.

## Consultar la auditoría

```bash
curl "http://127.0.0.1:8000/api/v1/audit-logs?limit=20&offset=0" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Solo un administrador puede consultar la auditoría. El resultado está limitado al tenant del token y se ordena de más reciente a más antiguo.

Respuesta `200`:

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

## Campos

| Campo | Descripción |
| --- | --- |
| `id` | UUID de la entrada. |
| `actor_user_id` | Usuario que ejecutó la acción; puede ser `null` si el usuario fue eliminado. |
| `action` | Nombre estable de la acción. |
| `entity_type` | Tipo de entidad afectada. |
| `entity_id` | Identificador de la entidad afectada. |
| `previous_state` | Estado anterior, o `null` si no aplica. |
| `new_state` | Estado nuevo, o `null` si no aplica. |
| `correlation_id` | Identificador de trazabilidad de la petición que originó la entrada. |
| `created_at` | Fecha y hora UTC. |

## Acciones registradas

| Acción | Origen |
| --- | --- |
| `tenant.created` | Registro público de un tenant. |
| `user.created` | Alta del administrador inicial y de nuevos usuarios. |
| `user.updated` | Cambio de nombre o estado de un usuario. |
| `tenant.config.updated` | Cambio de configuración del tenant. |
| `tenant.exchange_rates.replaced` | Reemplazo de la tabla de tasas. |
| `account.created` | Apertura de una cuenta. |
| `account.status.updated` | Cambio de estado de una cuenta. |

Las operaciones financieras no se escriben en la auditoría administrativa: se registran en la tabla de transacciones y se consultan con `GET /api/v1/transactions`. Esta separación evita duplicar el historial financiero.

## Inmutabilidad

- No existen endpoints para modificar ni borrar entradas de auditoría.
- La tabla es de solo adición desde la API.
- Las entradas se filtran siempre por `tenant_id`.
- Los cambios de configuración guardan `previous_state` y `new_state` para poder reconstruir la diferencia.

La inmutabilidad es lógica y de aplicación: un acceso directo a SQLite con permisos de escritura podría modificar la tabla. Para una garantía criptográfica o de base de datos habría que añadir sellado o permisos externos, que no forman parte de este proyecto.
