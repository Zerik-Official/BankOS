# Despliegue

BankOS se empaqueta como una imagen Docker con Uvicorn y SQLite. El repositorio incluye `Dockerfile` y `compose.yaml`.

## Docker Compose

1. Crea el archivo de entorno:

   ```bash
   cp .env.example .env
   ```

2. Cambia al menos `JWT_SECRET_KEY`.

3. Construye y arranca:

   ```bash
   docker compose up --build
   ```

4. Comprueba:

   ```bash
   curl http://127.0.0.1:8000/health
   curl http://127.0.0.1:8000/health/ready
   ```

5. Detén el stack:

   ```bash
   docker compose down
   ```

La API escucha en el puerto `8000`. La base se guarda en el volumen `bankos-data`, montado en `/app/data`. El `compose.yaml` fuerza `DATABASE_URL=sqlite:////app/data/bankos.db`.

Para borrar también los datos:

```bash
docker compose down -v
```

## Imagen

El `Dockerfile` usa `python:3.12-slim`, instala `requirements.txt`, copia `app/` y ejecuta:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

No copia tests, documentación ni scripts. El contenedor escribe logs en stdout.

## Base de datos y esquema

- SQLite es la base objetivo, tanto local como en Docker.
- El esquema se crea con `Base.metadata.create_all` en el arranque.
- No se usa Alembic.
- Si cambia el esquema de una base existente, hay que aplicar la migración manualmente o recrear la base.
- Haz copias de seguridad del archivo SQLite o del volumen antes de actualizar.

## Un solo worker

Uvicorn arranca con un worker por defecto. **No aumentes `--workers`** sin cambiar antes:

- el rate limiting en memoria;
- el lock en memoria de idempotencia.

La unicidad de las claves sigue protegida por la base de datos, pero el comportamiento concurrente y los límites no están diseñados para varios procesos. Para escalar horizontalmente hace falta un almacén compartido, por ejemplo Redis, y una revisión del diseño.

## Variables de entorno en producción

| Variable | Recomendación |
| --- | --- |
| `JWT_SECRET_KEY` | Valor largo, aleatorio y fuera del repositorio. |
| `ENVIRONMENT` | `production`. |
| `DOCS_ENABLED` | `false` si no quieres exponer Swagger/OpenAPI. |
| `CORS_ORIGINS` | Solo los orígenes reales del frontend. |
| `DATABASE_URL` | Ruta del volumen persistente. |
| `RATE_LIMIT_*` | Ajusta según el tráfico esperado. |
| `WEBHOOK_TIMEOUT_SECONDS` | Segundos por intento de webhook; súbelo si tu endpoint es lento. |

No se incluyen secretos en la imagen ni en el repositorio. `.env` está ignorado por Git.

## Salud y observabilidad

| Ruta | Uso |
| --- | --- |
| `GET /health` | Liveness: el proceso responde. |
| `GET /health/ready` | Readiness: la base responde a `SELECT 1`. |

Los logs incluyen el `correlation_id` de cada petición. La API devuelve `X-Correlation-ID` en todas las respuestas.

## CI/CD

El repositorio incluye dos workflows de GitHub Actions:

- `backend.yml`: en push y pull request a `dev` y `main`, instala dependencias y ejecuta `ruff check .`, `ruff format --check .` y `python -m pytest`.
- `docs.yml`: valida la documentación con `mkdocs build --strict` en pull request y push a `dev` y `main`, y publica el sitio en GitHub Pages en cada push a `dev` o `main`, anidado en `/BankOS/docs/` y con una redirección desde la raíz del sitio.

No hay workflow de despliegue de la API ni secretos de despliegue. La publicación del backend queda fuera del alcance de estos workflows.

## Checklist de producción

- [ ] `JWT_SECRET_KEY` cambiado y almacenado como secreto.
- [ ] `DOCS_ENABLED=false` si no se necesita Swagger público.
- [ ] `CORS_ORIGINS` limitado a los orígenes reales.
- [ ] Volumen de SQLite con copias de seguridad.
- [ ] Un solo worker de Uvicorn.
- [ ] HTTPS terminado en un proxy inverso.
- [ ] Logs recolectados y `X-Correlation-ID` visible.
- [ ] Webhooks apuntando a endpoints HTTPS propios.
- [ ] Límites de peticiones ajustados al tráfico.

## Frontend

El frontend y la aplicación móvil no forman parte de este repositorio ni de este despliegue. BankOS expone únicamente la API.
