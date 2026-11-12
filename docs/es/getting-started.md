# Primeros pasos

Esta guía instala BankOS en local, configura el entorno y ejecuta la API, los tests y la documentación.

## Requisitos

| Herramienta | Versión | Uso |
| --- | --- | --- |
| Python | 3.12 o superior | API, tests y documentación |
| Git | 2.40 o superior | Control de versiones |
| Docker Engine + Compose | Opcional | Ejecución en contenedor |
| curl | Opcional | Ejemplos de la API |

En Windows se recomienda Git Bash. Los comandos de esta guía usan el ejecutable del entorno virtual en `.venv/Scripts/python`. En Linux y macOS la ruta equivalente es `.venv/bin/python`.

## Instalación local

1. Clona el repositorio y entra en él:

   ```bash
   git clone https://github.com/Zerik-Official/BankOS
   cd BankOS
   ```

2. Crea el entorno virtual e instala las dependencias:

   ```bash
   python -m venv .venv
   .venv/Scripts/python -m pip install --upgrade pip
   .venv/Scripts/python -m pip install -r requirements.txt pytest ruff
   ```

3. Crea el archivo de entorno:

   ```bash
   cp .env.example .env
   ```

   Cambia al menos `JWT_SECRET_KEY` por un valor largo y aleatorio. El resto de valores funciona para desarrollo local.

4. Arranca la API:

   ```bash
   .venv/Scripts/python -m uvicorn app.main:app --reload
   ```

   La API queda disponible en <http://127.0.0.1:8000>. Al arrancar se crea el archivo `data/bankos.db` y el esquema de base de datos si no existe.

5. Comprueba el estado:

   ```bash
   curl http://127.0.0.1:8000/health
   curl http://127.0.0.1:8000/health/ready
   ```

6. Abre la referencia interactiva:

   - Swagger UI: <http://127.0.0.1:8000/docs>
   - ReDoc: <http://127.0.0.1:8000/redoc>
   - OpenAPI: <http://127.0.0.1:8000/openapi.json>

## Datos de demostración

El script `scripts/seed_demo.py` crea dos tenants de demostración con administradores, clientes, cuentas y saldos iniciales. Es idempotente: se puede ejecutar varias veces sin duplicar datos.

```bash
.venv/Scripts/python -m scripts.seed_demo
```

El script imprime al final los correos, la contraseña común de demostración y los números de cuenta. No usa datos reales.

| Tenant | Moneda base | Comisión |
| --- | --- | --- |
| `acme` | USD | Porcentual 2 % |
| `globex` | EUR | Fija 1.50 |

Ambos tenants reciben las tasas USD→EUR `0.900000` y EUR→USD `1.100000`.

## Tests y lint

```bash
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

Los tests usan una base SQLite separada (`data/test_bankos.db`) y recrean el esquema para cada prueba.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

La API escucha en <http://127.0.0.1:8000> y guarda la base en el volumen `bankos-data`. Consulta [Despliegue](deployment.md) para los detalles y las limitaciones operativas.

## Documentación

```bash
.venv/Scripts/python -m pip install -r requirements-docs.txt
.venv/Scripts/python -m mkdocs serve
```

El sitio se sirve en <http://127.0.0.1:8000>. Para validarlo con enlaces estrictos:

```bash
.venv/Scripts/python -m mkdocs build --strict
```

## Siguiente paso

Continúa con [Configuración](configuration.md) para revisar las variables de entorno y la configuración de cada tenant.
