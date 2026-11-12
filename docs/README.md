# BankOS Documentation

The BankOS documentation is written in English and Spanish and is published with MkDocs Material at <https://zerik-official.github.io/BankOS/docs/>. Spanish is the default language and English is available under `/en/`.

## Serve the site locally

```bash
.venv/Scripts/python -m pip install -r requirements-docs.txt
.venv/Scripts/python -m mkdocs serve
```

Open <http://127.0.0.1:8000>. The same command works on Linux and macOS with `python -m mkdocs serve`.

## Validate the site

```bash
.venv/Scripts/python -m mkdocs build --strict
```

The build fails on broken links, missing navigation entries and other warnings.

## Structure

| Path | Content |
| --- | --- |
| `es/` | Spanish documentation, the default locale |
| `en/` | English documentation |
| `es/index.md` | Spanish home page |
| `en/index.md` | English home page |

Both folders contain the same pages so that every navigation entry has a translation.

## English

| Document | Content |
| --- | --- |
| [Overview](en/index.md) | Purpose of BankOS and how to navigate the documentation |
| [Getting started](en/getting-started.md) | Installation, environment and first run |
| [Configuration](en/configuration.md) | Environment variables and tenant settings |
| [Authentication](en/authentication.md) | Login, JWT claims, roles and rate limits |
| [Multi-tenancy](en/multi-tenancy.md) | Isolation model and tenant registration |
| [Accounts](en/accounts.md) | Account lifecycle, visibility and soft delete |
| [Operations](en/operations.md) | Deposits, withdrawals and transaction history |
| [Idempotency](en/idempotency.md) | Idempotency-Key contract and replay behaviour |
| [Transfers and rates](en/transfers.md) | Fees, quotes, conversion and exchange rates |
| [Audit](en/audit.md) | Immutable administrative audit log |
| [Webhooks](en/webhooks.md) | Transfer notifications and retry policy |
| [Errors](en/errors.md) | Error envelope, HTTP status codes and error codes |
| [Deployment](en/deployment.md) | Docker, SQLite and operational limitations |

## Español

| Documento | Contenido |
| --- | --- |
| [Introducción](es/index.md) | Propósito de BankOS y cómo navegar la documentación |
| [Primeros pasos](es/getting-started.md) | Instalación, entorno y primera ejecución |
| [Configuración](es/configuration.md) | Variables de entorno y configuración por tenant |
| [Autenticación](es/authentication.md) | Login, claims del JWT, roles y límites de peticiones |
| [Multi-tenencia](es/multi-tenancy.md) | Modelo de aislamiento y registro de tenants |
| [Cuentas](es/accounts.md) | Ciclo de vida, visibilidad y borrado lógico |
| [Operaciones](es/operations.md) | Depósitos, retiros e historial de transacciones |
| [Idempotencia](es/idempotency.md) | Contrato de Idempotency-Key y replay |
| [Transferencias y tasas](es/transfers.md) | Comisiones, cotizaciones, conversión y tasas |
| [Auditoría](es/audit.md) | Registro de auditoría administrativa inmutable |
| [Webhooks](es/webhooks.md) | Notificaciones de transferencia y reintentos |
| [Errores](es/errors.md) | Sobre de error, códigos HTTP y códigos internos |
| [Despliegue](es/deployment.md) | Docker, SQLite y limitaciones operativas |
