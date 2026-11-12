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

See the [technical documentation](docs/README.md) for details.

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

## Getting started

The [getting started guide](docs/en/getting-started.md) covers installation, demo data and local configuration. Quick start:

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

## Documentation

The documentation is built with MkDocs Material in English and Spanish and published at <https://zerik-official.github.io/BankOS/docs/>. To serve it locally:

```bash
.venv/Scripts/python -m pip install -r requirements-docs.txt
.venv/Scripts/python -m mkdocs serve
```

Start with the [English documentation](docs/en/index.md) or the [Spanish documentation](docs/es/index.md).

