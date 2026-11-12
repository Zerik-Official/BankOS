# Getting started

This guide installs BankOS locally, configures the environment and runs the API, the tests and the documentation.

## Requirements

| Tool | Version | Purpose |
| --- | --- | --- |
| Python | 3.12 or newer | API, tests and documentation |
| Git | 2.40 or newer | Version control |
| Docker Engine + Compose | Optional | Container execution |
| curl | Optional | API examples |

On Windows, Git Bash is recommended. The commands in this guide use the virtual environment executable at `.venv/Scripts/python`. On Linux and macOS the equivalent path is `.venv/bin/python`.

## Local installation

1. Clone the repository and enter it:

   ```bash
   git clone https://github.com/Zerik-Official/BankOS
   cd BankOS
   ```

2. Create the virtual environment and install the dependencies:

   ```bash
   python -m venv .venv
   .venv/Scripts/python -m pip install --upgrade pip
   .venv/Scripts/python -m pip install -r requirements.txt pytest ruff
   ```

3. Create the environment file:

   ```bash
   cp .env.example .env
   ```

   Change at least `JWT_SECRET_KEY` to a long random value. The rest of the values work for local development.

4. Start the API:

   ```bash
   .venv/Scripts/python -m uvicorn app.main:app --reload
   ```

   The API is available at <http://127.0.0.1:8000>. On startup it creates `data/bankos.db` and the database schema when missing.

5. Check the status:

   ```bash
   curl http://127.0.0.1:8000/health
   curl http://127.0.0.1:8000/health/ready
   ```

6. Open the interactive reference:

   - Swagger UI: <http://127.0.0.1:8000/docs>
   - ReDoc: <http://127.0.0.1:8000/redoc>
   - OpenAPI: <http://127.0.0.1:8000/openapi.json>

## Demo data

The `scripts/seed_demo.py` script creates two demo tenants with administrators, clients, accounts and initial balances. It is idempotent: it can run several times without duplicating data.

```bash
.venv/Scripts/python -m scripts.seed_demo
```

The script prints the emails, the shared demo password and the account numbers. It does not use real data.

| Tenant | Base currency | Commission |
| --- | --- | --- |
| `acme` | USD | Percentage 2 % |
| `globex` | EUR | Fixed 1.50 |

Both tenants receive the rates USD→EUR `0.900000` and EUR→USD `1.100000`.

## Tests and lint

```bash
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

The tests use a separate SQLite database (`data/test_bankos.db`) and recreate the schema for every test.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The API listens on <http://127.0.0.1:8000> and stores the database in the `bankos-data` volume. See [Deployment](deployment.md) for details and operational limitations.

## Documentation

```bash
.venv/Scripts/python -m pip install -r requirements-docs.txt
.venv/Scripts/python -m mkdocs serve
```

The site is served at <http://127.0.0.1:8000>. To validate it with strict links:

```bash
.venv/Scripts/python -m mkdocs build --strict
```

## Next step

Continue with [Configuration](configuration.md) to review the environment variables and the per-tenant settings.
