# Configuración

BankOS se configura en dos niveles: variables de entorno del proceso y configuración persistida por tenant.

## Variables de entorno

Copia `.env.example` a `.env` y ajusta los valores. La aplicación lee el archivo `.env` al arrancar.

| Variable | Por defecto | Descripción |
| --- | --- | --- |
| `APP_NAME` | `BankOS API` | Nombre visible de la API y metadatos de OpenAPI. |
| `ENVIRONMENT` | `local` | Entorno de ejecución. Se registra en los logs de arranque. |
| `DOCS_ENABLED` | `true` | Expone `/docs`, `/redoc` y `/openapi.json`. En producción puede desactivarse. |
| `LOG_LEVEL` | `INFO` | Nivel mínimo de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `DATABASE_URL` | `sqlite:///./data/bankos.db` | URL de SQLAlchemy. En Docker se usa `sqlite:////app/data/bankos.db`. |
| `JWT_SECRET_KEY` | Valor inseguro de desarrollo | Clave HMAC para firmar y verificar los JWT. **Debe cambiarse**. |
| `JWT_ALGORITHM` | `HS256` | Algoritmo de firma del token. |
| `JWT_EXPIRES_MINUTES` | `60` | Vida del token de acceso en minutos. |
| `CORS_ORIGINS` | `http://localhost:8000,http://localhost:5173` | Orígenes permitidos, separados por comas. |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `10` | Intentos de login permitidos por IP y minuto. |
| `RATE_LIMIT_FINANCIAL_PER_MINUTE` | `30` | Operaciones financieras permitidas por usuario y tenant y minuto. |
| `RATE_LIMIT_IP_PER_MINUTE` | `120` | Límite global por IP y minuto para las rutas `/api/v1`. |
| `WEBHOOK_TIMEOUT_SECONDS` | `5` | Timeout en segundos de cada intento de entrega de webhooks. Debe ser mayor que 0. Se lee al importar la aplicación; un cambio requiere reiniciar el proceso. |

Los límites de peticiones se guardan en memoria y se leen al importar la aplicación. Un cambio requiere reiniciar el proceso.

## Ejemplo de `.env`

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

## Configuración por tenant

Cada tenant guarda su propia configuración. Se consulta con `GET /api/v1/tenants/me` y se modifica con `PATCH /api/v1/tenants/me`. Solo un administrador puede modificar la configuración.

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `name` | Texto | Nombre de la institución. |
| `slug` | Texto | Identificador único, inmutable tras el registro. |
| `base_currency` | Moneda de 3 letras | Moneda principal declarada por el tenant. No restringe las monedas de las cuentas. |
| `max_transaction_amount` | Dinero | Importe máximo por operación, expresado en la moneda de la operación. Por defecto `1000000.00`. |
| `commission_type` | `percentage` o `fixed` | Forma de calcular la comisión de transferencias salientes. |
| `commission_value` | Decimal | Porcentaje (por ejemplo `2` significa 2 %) o importe fijo en la moneda origen. |
| `webhook_url` | URL HTTP/HTTPS o `null` | Endpoint que recibe el evento `transfer.received`. |
| `is_active` | Booleano | Permite desactivar el tenant. Un tenant inactivo no puede autenticar usuarios. |

### Actualizar la configuración

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

Respuesta:

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

Solo se modifican los campos enviados. Para borrar el webhook, envía `"webhook_url": null`.

### Tasas de cambio

La tabla de tasas es estática y pertenece al tenant. Se consulta con `GET /api/v1/tenants/me/exchange-rates` y se reemplaza completa con `PUT /api/v1/tenants/me/exchange-rates`.

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

Reglas:

- Cada par `source_currency` + `target_currency` debe ser único.
- No se permite convertir una moneda a sí misma.
- La tasa debe ser positiva y admite hasta 6 decimales.
- La tabla admite hasta 100 pares.
- El reemplazo completo queda registrado en auditoría.

## Base de datos

SQLite es la base objetivo, tanto en local como en Docker. El esquema se crea con `Base.metadata.create_all` al arrancar la aplicación. No se usa Alembic. Si cambia el esquema de una base existente, hay que aplicar la migración manualmente o recrear la base.

La base local vive en `data/bankos.db`. En Docker vive en `/app/data/bankos.db`, dentro del volumen `bankos-data`.
