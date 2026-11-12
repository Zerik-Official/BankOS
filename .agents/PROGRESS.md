# BankOS — Estado del proyecto y traspaso

> Documento de continuidad. Última actualización: 2026-11-12.
> Léelo completo antes de tocar código. El contexto funcional original está en
> `.vscode/CONTEXT.md` y las reglas de trabajo en `.agents/AGENTS.md`.

## 1. Resumen

BankOS es una plataforma bancaria multi-tenant como servicio. Este repositorio
contiene **solo el backend** (FastAPI + SQLAlchemy + SQLite). El frontend
(Jinja2 + Tailwind CDN + Font Awesome) lo desarrolla otra persona y **no forma
parte de este trabajo**.

- Rama de trabajo: `dev`.
- No se ha creado **ningún commit** en esta sesión. El usuario pidió
  explícitamente no commitear hasta su autorización.
- El backend está funcionalmente completo, la suite pasa (**18 tests**) y la
  documentación bilingüe construye con `mkdocs build --strict`.

## 2. Estado general

| Bloque | Estado |
| --- | --- |
| Configuración del proyecto (pyproject, requirements, .env.example, Docker) | Hecho |
| Núcleo (`app/core`) | Hecho |
| Modelos, tipos de BD y sesión | Hecho |
| Repositorios con filtro por tenant | Hecho |
| Esquemas Pydantic | Hecho |
| Servicios de negocio | Hecho |
| Routers `/api/v1` + `main.py` | Hecho |
| Tests de auth y aislamiento | Hecho |
| Tests de transferencias/idempotencia | Hecho |
| Ejecución de pytest y corrección de fallos | Hecho (18 passed) |
| `scripts/seed_demo.py` | Hecho y verificado dos veces |
| Documentación MkDocs ES/EN | Hecho (13 páginas por idioma) |
| `README.md` / `README.es.md` | Hecho |
| CI/CD (`.github/workflows`) | Hecho |

## 3. Lo que ya está hecho

### 3.1 Entorno y configuración

- `pyproject.toml`: paquete `bankos-api`, Python >= 3.12, ruff con
  `line-length = 100`, reglas `E,F,I,B,UP` e `ignore = ["B008","UP046","UP047"]`
  (B008 porque FastAPI declara dependencias en defaults; UP046/UP047 porque se
  conserva la forma clásica `Generic[...]`). pytest con `testpaths = ["tests"]`.
- `requirements.txt`, `.env.example`, `.gitignore`, `.dockerignore`,
  `Dockerfile`, `compose.yaml`.
- `.venv` local ya creado con las dependencias instaladas
  (FastAPI 0.162.5, SQLAlchemy 2.1.8, pytest, ruff).

### 3.2 Núcleo (`app/core`)

- `config.py`: `Settings` con pydantic-settings; BD por defecto
  `sqlite:///./data/bankos.db`, JWT HS256, CORS, límites de rate limit.
- `security.py`: JWT con claims `tenant_id`, `user_id`, `role`; hashing de
  contraseñas PBKDF2-HMAC-SHA256 (stdlib, 260 000 iteraciones).
- `errors.py`: jerarquía `BankOSError` con códigos (`NOT_FOUND`,
  `FORBIDDEN`, `UNAUTHENTICATED`, `IDEMPOTENCY_IN_PROGRESS`, etc.).
- `correlation.py` + middleware en `main.py`: `X-Correlation-ID` de entrada o
  generado, se devuelve en todas las respuestas.
- `rate_limit.py`: ventanas en memoria para login (por IP), operaciones
  financieras (por usuario+tenant) y límite global por IP.
- `idempotency.py`: validación del header UUID, locks en memoria y TTL 24 h.
- `principal.py`: `Principal` con `is_admin`, `ensure_admin`.
- `logging.py`, `clock.py`, `serialization.py`.

### 3.3 Persistencia

- `app/db/types.py`: `Money` (centavos) y `Rate` (6 decimales) como enteros
  escalados mediante `TypeDecorator`.
- `app/db/session.py`: engine SQLite con `PRAGMA foreign_keys=ON` y
  `create_schema()` (`create_all`, sin Alembic).
- `app/models/`: `Tenant`, `ExchangeRate`, `User`, `Account`, `Transaction`,
  `AuditLog`, `IdempotencyRecord`; enums como `StrEnum`.
- `app/repositories/`: todos reciben `tenant_id` y filtran por él.

### 3.4 API disponible (24 rutas, visibles en `/docs`)

- `GET /`, `GET /health`, `GET /health/ready`
- `POST /api/v1/tenants` (registro público), `GET|PATCH /api/v1/tenants/me`,
  `GET|PUT /api/v1/tenants/me/exchange-rates`
- `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- `POST|GET /api/v1/users`, `GET|PATCH /api/v1/users/{user_id}`
- `POST|GET /api/v1/accounts`, `GET /api/v1/accounts/{account_id}`,
  `PATCH /api/v1/accounts/{account_id}/status` (soft delete),
  `POST /api/v1/accounts/{account_id}/deposits`,
  `POST /api/v1/accounts/{account_id}/withdrawals`
- `POST /api/v1/transfers/quote`, `POST /api/v1/transfers`
- `GET /api/v1/transactions`, `GET /api/v1/transactions/{transaction_id}`
- `GET /api/v1/audit-logs`

Todas las respuestas usan el sobre estándar (`success`, `code`, `message`,
`data`, `correlation_id`) o el sobre de error (`success: false`, `code`,
`message`, `details`, `correlation_id`).

### 3.5 Reglas de negocio implementadas

- Aislamiento: el `tenant_id` sale del JWT y todo repositorio filtra por él.
  Un recurso de otro tenant responde **404** (`NOT_FOUND`), incluso para
  administradores.
- Roles: `administrator` (gestiona usuarios, cuentas, configuración) y
  `client` (solo ve y opera sus propias cuentas).
- Idempotencia obligatoria en depósitos, retiros y transferencias:
  `Idempotency-Key` debe ser UUID (`MISSING_IDEMPOTENCY_KEY` /
  `INVALID_IDEMPOTENCY_KEY`, 422). Se guarda el cuerpo y código originales;
  un replay devuelve exactamente eso con `X-Idempotent-Replayed: true`.
  Una petición concurrente con la misma clave responde 409
  (`IDEMPOTENCY_IN_PROGRESS`). TTL 24 h. Si la operación falla por regla de
  negocio, se guarda una transacción `status=error` y **se libera la clave**
  para permitir reintento.
- Comisión configurable por tenant: fija o porcentual, cobrada en la moneda
  origen.
- Multimoneda: tabla estática de tasas (`PUT .../exchange-rates`), se usa la
  tasa directa o la inversa; error `EXCHANGE_RATE_NOT_FOUND` si no existe.
  Límite `max_transaction_amount` validado contra la moneda de la operación.
- Historial paginado con filtros (`limit`, `offset`, `type`, `status`,
  `account_id`, `date_from`, `date_to`) y visibilidad limitada al cliente.
- Auditoría inmutable de acciones relevantes (`tenant.created`,
  `user.created`, `tenant.config.updated`, operaciones, etc.).
- Webhooks con `BackgroundTasks` + httpx (3 intentos), evento
  `transfer.received`, cabecera `X-Correlation-ID`.
- `POST /transfers/quote` devuelve `fee`, `total_debit`, `exchange_rate`,
  `converted_amount`, monedas; no mueve fondos.

## 4. Tests

### 4.1 Ya escritos

- `tests/conftest.py`: fija variables de entorno **antes** de importar `app`
  (BD `sqlite:///./data/test_bankos.db`, límites de rate limit altos), crea y
  borra el esquema por test y entrega un `TestClient` con `lifespan`.
- `tests/helpers.py`: `register_tenant`, `login`, `auth`, `create_client_user`,
  `create_account`, `deposit`, `balance`.
- `tests/test_auth.py`: login correcto/incorrecto, token inválido, `/auth/me`.
- `tests/test_isolation.py`: lectura y depósito entre tenants, visibilidad de
  cuentas para clientes, listado de usuarios prohibido, auditoría por tenant.

### 4.2 `tests/test_transfers.py` (hecho)

Casos cubiertos:

1. Transferencia misma moneda con comisión porcentual 2: depósito 1000 en
   origen, transferir 100 → origen `898.00`, destino `100.00`, `fee` `2.00`,
   `exchange_rate` `1.000000`.
2. Falta `Idempotency-Key` → 422 `MISSING_IDEMPOTENCY_KEY`.
3. Clave no UUID → 422 `INVALID_IDEMPOTENCY_KEY`.
4. Replay: dos peticiones con la misma clave y cuerpo → segunda respuesta
   idéntica (mismo `data.id`), cabecera `X-Idempotent-Replayed: true` y
   saldos sin cambios.
5. Clave en `in_progress` → 409 `IDEMPOTENCY_IN_PROGRESS`. Se puede simular
   insertando un `IdempotencyRecord` con `SessionLocal` usando los UUID del
   tenant y del admin.
6. Fallo de negocio con clave (fondos insuficientes) → 422
   `INSUFFICIENT_FUNDS`; la clave queda liberada y el reintento con la misma
   clave funciona tras depositar. Debe existir una transacción `error`.
7. Multimoneda: tasa USD→EUR `0.900000`, transferir 100 USD → destino
   `90.00 EUR`, origen `898.00 USD`, `exchange_rate` `0.900000`.
8. `POST /transfers/quote` devuelve `fee`, `total_debit`, `exchange_rate`,
   `converted_amount` sin mover saldos.

### 4.3 Riesgo conocido, resuelto

`tests/test_isolation.py::test_audit_logs_are_tenant_scoped` esperaba
`acme=2` y `globex=1`, pero registrar un tenant genera dos registros
(`tenant.created` y `user.created`). Se corrigió la expectativa a
`acme=3` y `globex=2` y se añadieron aserciones sobre las acciones
`tenant.created` y `user.created`. No se tocó el servicio.

### 4.4 Resultado real de la suite

```
18 passed, 1 warning in 101.54s (0:01:41)
```

El único warning es de Starlette: `Using httpx with starlette.testclient is
deprecated; install httpx2 instead`. Viene de la dependencia, no del código del
proyecto; no se ha silenciado.

## 5. Decisiones técnicas que NO se deben revertir sin consultar

1. **Sin Alembic**: el esquema se crea con `Base.metadata.create_all` en el
   lifespan. Es deliberado ("no nos vamos a complicar").
2. **Dinero y tasas como enteros escalados** (`app/db/types.py`), no `Float`.
   `Money` = centavos, `Rate` = 6 decimales.
3. **SQLite** es la BD objetivo, tanto local como en Docker (volumen
   `/app/data`). No introducir Postgres.
4. **Hashing PBKDF2 de la stdlib**, sin dependencias externas (bcrypt, argon2).
5. **Rate limiting en memoria**: solo es correcto con un worker. Si se
   despliega con varios workers/procesos habría que moverlo a un almacén
   compartido; documentarlo como limitación, no "arreglarlo" sin pedirlo.
6. **Idempotencia con registro en BD** `in_progress`/`completed`, lock en
   memoria y replay del cuerpo original (se ignora el body nuevo). El registro
   se borra cuando la operación falla por regla de negocio.
7. **Los fallos de negocio se persisten** como `Transaction(status=error)` con
   `error_code`; las operaciones exitosas son `success`.
8. **Comisión en la moneda origen**; la conversión se aplica al monto enviado,
   no a la comisión.
9. **Webhooks sin HMAC**, con `BackgroundTasks`, 3 intentos y
   `X-Correlation-ID`. No bloquear la respuesta por el webhook.
10. **Ruff**: no quitar los `ignore` de `pyproject.toml` ni añadir `noqa`
    masivos. `B008` es el patrón normal de FastAPI.
11. **Rutas en plural y prefijo `/api/v1`**; `tenants` y `health` se montan en
    `app/main.py`, el resto en `app/api/v1/router.py`.

## 6. Tareas de la sesión (todas completadas)

### 6.1 `tests/test_transfers.py` (hecho)

Crear el archivo con los 8 casos de la sección 4.2 usando los helpers
existentes. Para la tasa de cambio, `PUT /api/v1/tenants/me/exchange-rates`
con `{"rates": [{"source_currency": "USD", "target_currency": "EUR",
"rate": "0.900000"}]}` usando el token del admin.

### 6.2 Ejecutar la suite y corregir (hecho)

```
.venv/Scripts/python -m pytest
```

- Corregir primero la aserción de auditoría descrita en 4.3.
- No debilitar aserciones ni añadir `skip` para que pase: arreglar la causa.
- Repetir solo los tests afectados tras cada corrección.
- Al terminar, dejar la suite en verde y anotar aquí el resultado exacto
  (nº de tests y fecha).

### 6.3 `scripts/seed_demo.py` (hecho)

Script idempotente (puede ejecutarse varias veces sin duplicar) que cree dos
tenants demo mediante los servicios/modelos:

- `acme` (USD, comisión porcentual 2) y `globex` (EUR, comisión fija 1.50).
- Tasas: USD→EUR 0.900000 y EUR→USD 1.100000 por tenant.
- Un admin y dos clientes por tenant, cada cliente con cuenta en la moneda
  base y en la otra moneda.
- Saldos iniciales vía depósitos idempotentes o asignación directa.
- Imprimir al final credenciales demo (emails y contraseña) y los números de
  cuenta. No usar datos reales.

### 6.4 Documentación bilingüe con MkDocs (hecho)

Seguir la estructura de `.vscode/Motorix/` (referencia, no copiar contenido):

- `mkdocs.yml` con `material`, `mkdocs-static-i18n` (ES por defecto, EN en
  `docs/en`), navegación y `site_url` provisional
  `https://zerik-official.github.io/BankOS/docs/`.
- `requirements-docs.txt` (`mkdocs-material`, `mkdocs-static-i18n`).
- `docs/es/` y `docs/en/`: portada, instalación/ejecución, configuración,
  autenticación, multi-tenancy, cuentas, operaciones, idempotencia,
  transferencias y tasas, auditoría, webhooks, errores, despliegue.
- `docs/README.md` explicando cómo levantar el sitio (`mkdocs serve`).
- Diagramas en Mermaid, ejemplos `curl` reales con el sobre de respuesta.
- Los markdown deben reflejar el comportamiento real de la sección 3; no
  documentar endpoints o códigos que no existan.

### 6.5 `README.md` y `README.es.md` (hecho)

Usar como plantilla los README de `.vscode/Motorix/` (badges, stack, quick
start, variables de entorno, estructura, endpoints, tests, Docker, docs).
El usuario colocará las imágenes; dejar rutas/alt de imagen preparados y no
inventar capturas. `README.md` en inglés y `README.es.md` en español, con
enlaces cruzados.

### 6.6 CI/CD (`.github/workflows/`) (hecho)

- `backend.yml`: en push/PR a `dev` y `main`; Python 3.12; instalar
  `requirements.txt` + `pytest` + `ruff`; ejecutar `ruff check .`,
  `ruff format --check .` y `pytest`.
- `docs.yml`: construir con `mkdocs build --strict` y publicar el sitio en
  GitHub Pages (artifact + `gh-pages`/Pages action) desde `main`.
- No añadir despliegues de la API ni secretos que el usuario no haya dado.

### 6.7 Verificación final (hecho)

Resultado real del 2026-11-12:

```
.venv/Scripts/python -m ruff check .          -> All checks passed!
.venv/Scripts/python -m ruff format --check . -> 100 files already formatted
.venv/Scripts/python -m pytest                -> 18 passed, 1 warning in 101.54s
.venv/Scripts/python -m mkdocs build --strict -> ES + EN construidos sin warnings
```

**No hacer commits** hasta que el usuario lo autorice; cuando lo haga, seguir
`.agents/AGENTS.md`: conventional commits y **un commit por archivo**.

## 7. Cómo ejecutar el proyecto

Entorno: Windows + Git Bash, Python 3.12, venv en `.venv`.

```bash
# Dependencias (ya instaladas)
.venv/Scripts/python -m pip install -r requirements.txt pytest ruff

# Arrancar la API (crea data/bankos.db y las tablas)
.venv/Scripts/python -m uvicorn app.main:app --reload

# Swagger / OpenAPI
# http://127.0.0.1:8000/docs  y  http://127.0.0.1:8000/openapi.json

# Tests
.venv/Scripts/python -m pytest

# Lint y formato
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .

# Docker
docker compose up --build
```

Variables de entorno: copiar `.env.example` a `.env` y cambiar al menos
`JWT_SECRET_KEY`.

## 8. Trampas y notas técnicas

- **Timestamps de SQLite vuelven naive** al leerlos: `app/services/transaction.py`
  usa `_as_aware()` para comparar con `utc_now()`. No comparar directamente.
- **FastAPI 0.162.5** no expone las rutas incluidas como objetos planos en
  `app.routes`; para inspeccionarlas usar `app.openapi()["paths"]`.
- **Escritura de archivos con CRLF**: `write_file` puede fallar con archivos
  con finales CRLF. Usar `cat > archivo <<'EOF'` si ocurre.
- **`.agents/PROGRESS.md` se versiona** junto al repositorio. `.vscode/*` sigue
  ignorado; si se añade documentación local ahí, no se subirá.
- **`.env.example`** debe poder copiarse a `.env` tal cual; solo hay que
  reemplazar `JWT_SECRET_KEY`.
- **Nunca** registrar contraseñas, tokens, `JWT_SECRET_KEY` ni cuerpos
  sensibles en logs o auditoría.
- Los tests fuerzan límites de rate limit altos en `tests/conftest.py`; no
  subirlos en producción.
- Orden y agrupación de imports y type hints son obligatorios
  (`.agents/AGENTS.md`). Docstrings en inglés; respuestas al usuario en
  español.

## 9. Registro de la sesión (2026-11-12)

En esta sesión se completaron las tareas pendientes del backend. **No se ha
creado ningún commit.**

Trabajo realizado:

- `tests/test_transfers.py` con 8 casos: comisión 2 %, falta de clave, clave
  inválida, replay, 409 en progreso, liberación tras fallo de negocio,
  multimoneda USD→EUR 0.9 y quote.
- Aserción de auditoría corregida en `tests/test_isolation.py` (`acme=3`,
  `globex=2`, con aserciones de acciones).
- `scripts/seed_demo.py` + `scripts/__init__.py`, ejecutado dos veces con una
  SQLite temporal sin duplicar: 2 tenants, 6 usuarios, 8 cuentas y 8
  transacciones. La base temporal se eliminó.
- `mkdocs.yml`, `requirements-docs.txt`, `docs/README.md`, 13 páginas ES y 13
  páginas EN.
- `README.md` y `README.es.md` con badges, quick start, endpoints, tests,
  Docker y docs; rutas de imagen `.github/preview.en.png` /
  `.github/preview.es.png` preparadas sin capturas inventadas.
- `.github/workflows/backend.yml` y `.github/workflows/docs.yml`.

Verificación real:

- `ruff check .`: limpio.
- `ruff format --check .`: 100 archivos ya formateados.
- `pytest`: 18 passed, 1 warning en 101.54 s.
- `mkdocs build --strict`: ES y EN construidos en 3.75 s, sin warnings.

Limitaciones declaradas: no se ejecutó Docker ni se validó el despliegue real
en GitHub Pages; el workflow de docs se ha escrito pero no se ha ejecutado en
GitHub.

### Ajustes posteriores (misma fecha)

- `WEBHOOK_TIMEOUT_SECONDS` ya no está reservado: `deliver_webhook` lee
  `get_settings().webhook_timeout_seconds`, validado con `gt=0`. Comprobado con
  un valor de `2.5` en el entorno y un `httpx.post` simulado.
- `docs.yml` sigue el patrón de Motorix: valida en PR/push a `dev` y `main`,
  anida el sitio en `/BankOS/docs/`, escribe un `index.html` que redirige la
  raíz y despliega solo desde `main`.
- `AGENTS.md` incluye convenciones de PR: títulos, plantilla de descripción,
  labels, ramas y checklist previo.

## 10. Checklist para la siguiente IA

1. Leer `.vscode/CONTEXT.md`, `.agents/AGENTS.md` y este documento.
2. Revisar el diff completo antes de commitear.
3. **No commitear** hasta que el usuario lo autorice; entonces, conventional
   commits y un commit por archivo.
4. Si se autoriza, validar los workflows en GitHub y añadir las capturas
   reales en `.github/`.

## 11. Definición de "terminado"

- `ruff check .` y `ruff format --check .` limpios.
- `pytest` en verde con tests de auth, aislamiento, depósitos, retiros,
  transferencias, idempotencia, tasas/comisión y quote.
- Docs MkDocs ES/EN construyen con `--strict` y cubren todos los endpoints.
- README bilingüe con quick start documentado.
- CI configurado (workflows escritos; su ejecución real en GitHub queda
  pendiente de push).
- Sin secretos ni datos reales en el repositorio.
