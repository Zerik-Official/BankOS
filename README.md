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
  <img src=".github/preview.en.png" alt="BankOS API preview"/>
</p>

<p align="center">
  <a href="./README.es.md">Español</a> | <strong>English</strong>
</p>

BankOS is a multi-tenant banking platform as a service. Every financial institution runs as an independent tenant with its own users, accounts, currencies, commissions, exchange rates, business rules and audit records. This repository contains only the backend: a REST API built with FastAPI, SQLAlchemy and SQLite. The frontend and mobile application are developed separately.

## Tech stack

| Component | Stack | Responsibility |
| --- | --- | --- |
| API | FastAPI, Pydantic, Uvicorn | HTTP routes, validation, OpenAPI and background tasks |
| Persistence | SQLAlchemy, SQLite | Tenant-scoped repositories, scaled integer money and rates |
| Security | JWT HS256, PBKDF2-HMAC-SHA256 | Authentication, roles and password hashing |
| Reliability | Idempotency keys, correlation IDs, in-memory rate limiting | Safe retries, tracing and request protection |
| Delivery | Docker Compose, GitHub Actions, MkDocs Material | Local stack, CI and bilingual documentation |

## Repository structure

```text
bankos/
├── app/
│   ├── api/                   # Routes, dependencies and response envelopes
│   ├── core/                  # Config, security, errors, idempotency, rate limiting
│   ├── db/                    # Engine, session and scaled types
│   ├── models/                # SQLAlchemy models
│   ├── repositories/          # Tenant-scoped persistence
│   ├── schemas/               # Pydantic schemas
│   └── services/              # Business rules
├── tests/                     # Auth, isolation and transfer tests
├── scripts/                   # Idempotent demo seed
├── docs/
│   ├── en/                    # English documentation
│   └── es/                    # Spanish documentation
├── .github/workflows/         # Backend and documentation CI
├── compose.yaml
├── Dockerfile
├── mkdocs.yml
├── requirements.txt
├── requirements-docs.txt
└── .env.example
```

## Requirements

- Python 3.12 or newer
- Docker Engine with the Compose plugin (optional)
- curl (optional, for the examples)

## Quick start

1. Clone the repository and create the virtual environment:

   ```bash
   git clone https://github.com/Zerik-Official/BankOS
   cd BankOS
   python -m venv .venv
   .venv/Scripts/python -m pip install -r requirements.txt pytest ruff
   ```

2. Create the environment file and change at least `JWT_SECRET_KEY`:

   ```bash
   cp .env.example .env
   ```

3. Start the API:

   ```bash
   .venv/Scripts/python -m uvicorn app.main:app --reload
   ```

4. Open the API and the interactive reference:

   - API: <http://127.0.0.1:8000>
   - Swagger UI: <http://127.0.0.1:8000/docs>
   - Health: <http://127.0.0.1:8000/health>

5. Create demo data (idempotent, no real data):

   ```bash
   .venv/Scripts/python -m scripts.seed_demo
   ```

The seed creates the `acme` tenant (USD, 2 % commission) and the `globex` tenant (EUR, fixed 1.50 commission), with an administrator, two clients and two accounts per client. It prints the demo credentials and account numbers.

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `BankOS API` | API name and OpenAPI metadata |
| `ENVIRONMENT` | `local` | Execution environment |
| `DOCS_ENABLED` | `true` | Exposes `/docs`, `/redoc` and `/openapi.json` |
| `LOG_LEVEL` | `INFO` | Minimum logging level |
| `DATABASE_URL` | `sqlite:///./data/bankos.db` | SQLAlchemy database URL |
| `JWT_SECRET_KEY` | Insecure development value | HMAC key for JWT signing; must be changed |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRES_MINUTES` | `60` | Access token lifetime |
| `CORS_ORIGINS` | `http://localhost:8000,http://localhost:5173` | Allowed origins |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `10` | Login attempts per IP and minute |
| `RATE_LIMIT_FINANCIAL_PER_MINUTE` | `30` | Financial operations per user and tenant and minute |
| `RATE_LIMIT_IP_PER_MINUTE` | `120` | Global requests per IP and minute |
| `WEBHOOK_TIMEOUT_SECONDS` | `5` | Timeout in seconds for each webhook delivery attempt; must be greater than 0 |

## API overview

All responses use a standard envelope with `success`, `code`, `message`, `data` and `correlation_id`. Errors use `success: false`, `code`, `message`, `details` and `correlation_id`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service metadata |
| `GET` | `/health` | Liveness probe |
| `GET` | `/health/ready` | Readiness probe |
| `POST` | `/api/v1/tenants` | Register a tenant and its administrator |
| `GET` | `/api/v1/tenants/me` | Read the current tenant configuration |
| `PATCH` | `/api/v1/tenants/me` | Update the current tenant configuration |
| `GET` | `/api/v1/tenants/me/exchange-rates` | List the static exchange rates |
| `PUT` | `/api/v1/tenants/me/exchange-rates` | Replace the static exchange rates |
| `POST` | `/api/v1/auth/login` | Log in inside a tenant |
| `GET` | `/api/v1/auth/me` | Read the authenticated profile |
| `POST` | `/api/v1/users` | Create a user |
| `GET` | `/api/v1/users` | List users |
| `GET` | `/api/v1/users/{user_id}` | Read a user |
| `PATCH` | `/api/v1/users/{user_id}` | Update a user |
| `POST` | `/api/v1/accounts` | Open an account |
| `GET` | `/api/v1/accounts` | List accounts |
| `GET` | `/api/v1/accounts/{account_id}` | Read an account |
| `PATCH` | `/api/v1/accounts/{account_id}/status` | Change the account status |
| `POST` | `/api/v1/accounts/{account_id}/deposits` | Deposit money |
| `POST` | `/api/v1/accounts/{account_id}/withdrawals` | Withdraw money |
| `POST` | `/api/v1/transfers/quote` | Quote a transfer |
| `POST` | `/api/v1/transfers` | Execute a transfer |
| `GET` | `/api/v1/transactions` | List transaction history |
| `GET` | `/api/v1/transactions/{transaction_id}` | Read a transaction |
| `GET` | `/api/v1/audit-logs` | Read the administrative audit log |

Deposits, withdrawals and transfers require an `Idempotency-Key` UUID header. Replays return the original response with `X-Idempotent-Replayed: true`.

## Tests and lint

```bash
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

The suite covers authentication, tenant isolation, commissions, idempotency replay, in-progress conflicts, key release after business failures, multi-currency transfers and quotes.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The API listens on port `8000`. SQLite data is stored in the `bankos-data` volume at `/app/data/bankos.db`. See the [deployment guide](docs/en/deployment.md) for operational limitations.

## Documentation

The documentation is built with MkDocs Material in English and Spanish and published at <https://zerik-official.github.io/BankOS/docs/>. To serve it locally:

```bash
.venv/Scripts/python -m pip install -r requirements-docs.txt
.venv/Scripts/python -m mkdocs serve
```

Start with the [English documentation](docs/en/index.md) or the [Spanish documentation](docs/es/index.md).

## Limitations

- SQLite is the only supported database; there is no PostgreSQL setup.
- The schema is created with `create_all`; Alembic is not used.
- Rate limiting and the idempotency lock live in memory and assume one worker.
- There are no refresh tokens or session revocation.
- Webhooks are best effort: no HMAC, no persistent queue and no delivery log.
- The frontend and mobile application are not part of this repository.

## Screenshots

The preview images are expected at `.github/preview.en.png` and `.github/preview.es.png`. The maintainer will add the real captures.
