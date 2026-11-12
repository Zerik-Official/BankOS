<h1 align="center">
  BankOS
</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-111111?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/FastAPI-111111?style=for-the-badge&logo=fastapi">
  <img src="https://img.shields.io/badge/SQLAlchemy-111111?style=for-the-badge&logo=sqlalchemy">
  <img src="https://img.shields.io/badge/SQLite-111111?style=for-the-badge&logo=sqlite">
  <img src="https://img.shields.io/badge/JWT_HS256-111111?style=for-the-badge&logo=jsonwebtokens&logoColor=white">
  <img src="https://img.shields.io/badge/Docker-111111?style=for-the-badge&logo=docker">
  <img src="https://img.shields.io/badge/GitHub_Actions-111111?style=for-the-badge&logo=githubactions">
  <img src="https://img.shields.io/badge/MkDocs_Material-111111?style=for-the-badge&logo=materialformkdocs">
</p>

<p align="center">
  <img src=".github/preview.es.png" alt="Vista previa de la API de BankOS"/>
</p>

<p align="center">
  <strong>Español</strong> | <a href="./README.md">English</a>
</p>

BankOS es una plataforma bancaria multi-tenant como servicio. Cada institución financiera opera como un tenant independiente con sus propios usuarios, cuentas, divisas, comisiones, tasas de cambio, reglas de negocio y registros de auditoría. Este repositorio contiene solo el backend: una API REST construida con FastAPI, SQLAlchemy y SQLite. El frontend y la aplicación móvil se desarrollan por separado.

## Stack tecnológico

| Componente | Stack | Responsabilidad |
| --- | --- | --- |
| API | FastAPI, Pydantic, Uvicorn | Rutas HTTP, validación, OpenAPI y tareas en segundo plano |
| Persistencia | SQLAlchemy, SQLite | Repositorios por tenant, dinero y tasas como enteros escalados |
| Seguridad | JWT HS256, PBKDF2-HMAC-SHA256 | Autenticación, roles y hashing de contraseñas |
| Fiabilidad | Claves de idempotencia, correlation IDs, rate limiting en memoria | Reintentos seguros, trazabilidad y protección de peticiones |
| Entrega | Docker Compose, GitHub Actions, MkDocs Material | Stack local, CI y documentación bilingüe |

## Estructura del repositorio

```text
bankos/
├── app/
│   ├── api/                   # Rutas, dependencias y sobres de respuesta
│   ├── core/                  # Configuración, seguridad, errores, idempotencia, rate limiting
│   ├── db/                    # Engine, sesión y tipos escalados
│   ├── models/                # Modelos SQLAlchemy
│   ├── repositories/          # Persistencia filtrada por tenant
│   ├── schemas/               # Esquemas Pydantic
│   └── services/              # Reglas de negocio
├── tests/                     # Tests de auth, aislamiento y transferencias
├── scripts/                   # Seed de demostración idempotente
├── docs/
│   ├── en/                    # Documentación en inglés
│   └── es/                    # Documentación en español
├── .github/workflows/         # CI del backend y de la documentación
├── compose.yaml
├── Dockerfile
├── mkdocs.yml
├── requirements.txt
├── requirements-docs.txt
└── .env.example
```

## Requisitos

- Python 3.12 o superior
- Docker Engine con el plugin de Compose (opcional)
- curl (opcional, para los ejemplos)

## Puesta en marcha

1. Clona el repositorio y crea el entorno virtual:

   ```bash
   git clone https://github.com/Zerik-Official/BankOS
   cd BankOS
   python -m venv .venv
   .venv/Scripts/python -m pip install -r requirements.txt pytest ruff
   ```

2. Crea el archivo de entorno y cambia al menos `JWT_SECRET_KEY`:

   ```bash
   cp .env.example .env
   ```

3. Arranca la API:

   ```bash
   .venv/Scripts/python -m uvicorn app.main:app --reload
   ```

4. Abre la API y la referencia interactiva:

   - API: <http://127.0.0.1:8000>
   - Swagger UI: <http://127.0.0.1:8000/docs>
   - Salud: <http://127.0.0.1:8000/health>

5. Crea los datos de demostración (idempotente, sin datos reales):

   ```bash
   .venv/Scripts/python -m scripts.seed_demo
   ```

El seed crea el tenant `acme` (USD, comisión porcentual 2 %) y el tenant `globex` (EUR, comisión fija 1.50), con un administrador, dos clientes y dos cuentas por cliente. Imprime las credenciales demo y los números de cuenta.

## Variables de entorno

| Variable | Por defecto | Descripción |
| --- | --- | --- |
| `APP_NAME` | `BankOS API` | Nombre de la API y metadatos de OpenAPI |
| `ENVIRONMENT` | `local` | Entorno de ejecución |
| `DOCS_ENABLED` | `true` | Expone `/docs`, `/redoc` y `/openapi.json` |
| `LOG_LEVEL` | `INFO` | Nivel mínimo de logging |
| `DATABASE_URL` | `sqlite:///./data/bankos.db` | URL de base de datos de SQLAlchemy |
| `JWT_SECRET_KEY` | Valor inseguro de desarrollo | Clave HMAC para firmar JWT; debe cambiarse |
| `JWT_ALGORITHM` | `HS256` | Algoritmo de firma del JWT |
| `JWT_EXPIRES_MINUTES` | `60` | Vida del token de acceso |
| `CORS_ORIGINS` | `http://localhost:8000,http://localhost:5173` | Orígenes permitidos |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `10` | Intentos de login por IP y minuto |
| `RATE_LIMIT_FINANCIAL_PER_MINUTE` | `30` | Operaciones financieras por usuario y tenant y minuto |
| `RATE_LIMIT_IP_PER_MINUTE` | `120` | Peticiones globales por IP y minuto |
| `WEBHOOK_TIMEOUT_SECONDS` | `5` | Timeout en segundos de cada intento de entrega de webhooks; debe ser mayor que 0 |

## Resumen de la API

Todas las respuestas usan un sobre estándar con `success`, `code`, `message`, `data` y `correlation_id`. Los errores usan `success: false`, `code`, `message`, `details` y `correlation_id`.

| Método | Ruta | Propósito |
| --- | --- | --- |
| `GET` | `/` | Metadatos del servicio |
| `GET` | `/health` | Liveness |
| `GET` | `/health/ready` | Readiness |
| `POST` | `/api/v1/tenants` | Registrar un tenant y su administrador |
| `GET` | `/api/v1/tenants/me` | Leer la configuración del tenant actual |
| `PATCH` | `/api/v1/tenants/me` | Actualizar la configuración del tenant actual |
| `GET` | `/api/v1/tenants/me/exchange-rates` | Listar las tasas estáticas |
| `PUT` | `/api/v1/tenants/me/exchange-rates` | Reemplazar las tasas estáticas |
| `POST` | `/api/v1/auth/login` | Iniciar sesión dentro de un tenant |
| `GET` | `/api/v1/auth/me` | Leer el perfil autenticado |
| `POST` | `/api/v1/users` | Crear un usuario |
| `GET` | `/api/v1/users` | Listar usuarios |
| `GET` | `/api/v1/users/{user_id}` | Leer un usuario |
| `PATCH` | `/api/v1/users/{user_id}` | Actualizar un usuario |
| `POST` | `/api/v1/accounts` | Abrir una cuenta |
| `GET` | `/api/v1/accounts` | Listar cuentas |
| `GET` | `/api/v1/accounts/{account_id}` | Leer una cuenta |
| `PATCH` | `/api/v1/accounts/{account_id}/status` | Cambiar el estado de la cuenta |
| `POST` | `/api/v1/accounts/{account_id}/deposits` | Depositar dinero |
| `POST` | `/api/v1/accounts/{account_id}/withdrawals` | Retirar dinero |
| `POST` | `/api/v1/transfers/quote` | Cotizar una transferencia |
| `POST` | `/api/v1/transfers` | Ejecutar una transferencia |
| `GET` | `/api/v1/transactions` | Listar el historial de transacciones |
| `GET` | `/api/v1/transactions/{transaction_id}` | Leer una transacción |
| `GET` | `/api/v1/audit-logs` | Leer la auditoría administrativa |

Los depósitos, retiros y transferencias exigen la cabecera `Idempotency-Key` con un UUID. Los reintentos devuelven la respuesta original con `X-Idempotent-Replayed: true`.

## Tests y lint

```bash
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

La suite cubre autenticación, aislamiento por tenant, comisiones, replay de idempotencia, conflictos en progreso, liberación de clave tras fallos de negocio, transferencias multimoneda y cotizaciones.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

La API escucha en el puerto `8000`. Los datos SQLite se guardan en el volumen `bankos-data`, en `/app/data/bankos.db`. Consulta la [guía de despliegue](docs/es/deployment.md) para las limitaciones operativas.

## Documentación

La documentación se construye con MkDocs Material en inglés y español y se publica en <https://zerik-official.github.io/BankOS/docs/>. Para servirla en local:

```bash
.venv/Scripts/python -m pip install -r requirements-docs.txt
.venv/Scripts/python -m mkdocs serve
```

Empieza por la [documentación en español](docs/es/index.md) o la [documentación en inglés](docs/en/index.md).

## Limitaciones

- SQLite es la única base soportada; no hay configuración para PostgreSQL.
- El esquema se crea con `create_all`; no se usa Alembic.
- El rate limiting y el lock de idempotencia viven en memoria y asumen un worker.
- No hay refresh tokens ni revocación de sesiones.
- Los webhooks son de mejor esfuerzo: sin HMAC, sin cola persistente y sin log de entregas.
- El frontend y la aplicación móvil no forman parte de este repositorio.

## Capturas

Las imágenes de vista previa se esperan en `.github/preview.en.png` y `.github/preview.es.png`. El mantenedor añadirá las capturas reales.
