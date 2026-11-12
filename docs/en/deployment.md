# Deployment

BankOS is packaged as a Docker image with Uvicorn and SQLite. The repository includes a `Dockerfile` and a `compose.yaml`.

## Docker Compose

1. Create the environment file:

   ```bash
   cp .env.example .env
   ```

2. Change at least `JWT_SECRET_KEY`.

3. Build and start:

   ```bash
   docker compose up --build
   ```

4. Check:

   ```bash
   curl http://127.0.0.1:8000/health
   curl http://127.0.0.1:8000/health/ready
   ```

5. Stop the stack:

   ```bash
   docker compose down
   ```

The API listens on port `8000`. The database is stored in the `bankos-data` volume, mounted at `/app/data`. The `compose.yaml` forces `DATABASE_URL=sqlite:////app/data/bankos.db`.

To delete the data as well:

```bash
docker compose down -v
```

## Image

The `Dockerfile` uses `python:3.12-slim`, installs `requirements.txt`, copies `app/` and runs:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

It does not copy tests, documentation or scripts. The container writes logs to stdout.

## Database and schema

- SQLite is the target database both locally and in Docker.
- The schema is created with `Base.metadata.create_all` on startup.
- Alembic is not used.
- If the schema changes on an existing database, apply the migration manually or recreate the database.
- Back up the SQLite file or the volume before upgrading.

## Single worker

Uvicorn starts with one worker by default. **Do not increase `--workers`** without first changing:

- the in-memory rate limiting;
- the in-memory idempotency lock.

Key uniqueness is still protected by the database, but concurrency behaviour and limits are not designed for multiple processes. Horizontal scaling requires a shared store, for example Redis, and a design review.

## Production environment variables

| Variable | Recommendation |
| --- | --- |
| `JWT_SECRET_KEY` | Long random value, kept outside the repository. |
| `ENVIRONMENT` | `production`. |
| `DOCS_ENABLED` | `false` if you do not want to expose Swagger/OpenAPI. |
| `CORS_ORIGINS` | Only the real frontend origins. |
| `DATABASE_URL` | Path of the persistent volume. |
| `RATE_LIMIT_*` | Adjust to the expected traffic. |
| `WEBHOOK_TIMEOUT_SECONDS` | Seconds per webhook attempt; raise it if your endpoint is slow. |

No secrets are included in the image or the repository. `.env` is ignored by Git.

## Health and observability

| Route | Usage |
| --- | --- |
| `GET /health` | Liveness: the process responds. |
| `GET /health/ready` | Readiness: the database answers `SELECT 1`. |

Logs include the `correlation_id` of every request. The API returns `X-Correlation-ID` on every response.

## CI/CD

The repository includes two GitHub Actions workflows:

- `backend.yml`: on push and pull request to `dev` and `main`, installs dependencies and runs `ruff check .`, `ruff format --check .` and `python -m pytest`.
- `docs.yml`: validates the documentation with `mkdocs build --strict` on pull requests and pushes to `dev` and `main`, and publishes the site to GitHub Pages on every push to `dev` or `main`, nested under `/BankOS/docs/` and with a redirect from the site root.

There is no API deployment workflow and no deployment secrets. Publishing the backend is outside the scope of these workflows.

## Production checklist

- [ ] `JWT_SECRET_KEY` changed and stored as a secret.
- [ ] `DOCS_ENABLED=false` if public Swagger is not needed.
- [ ] `CORS_ORIGINS` limited to the real origins.
- [ ] SQLite volume with backups.
- [ ] One Uvicorn worker.
- [ ] HTTPS terminated at a reverse proxy.
- [ ] Logs collected and `X-Correlation-ID` visible.
- [ ] Webhooks pointing to your own HTTPS endpoints.
- [ ] Rate limits adjusted to the traffic.

## Frontend

The frontend and the mobile application are not part of this repository or this deployment. BankOS exposes only the API.
