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

Consulta la [documentación técnica](docs/README.md) para más detalles.

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

La [guía de primeros pasos](docs/es/getting-started.md) cubre la instalación, los datos demo y la configuración local. Inicio rápido:

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

## Documentación

La documentación se construye con MkDocs Material en inglés y español y se publica en <https://zerik-official.github.io/BankOS/docs/>. Para servirla en local:

```bash
.venv/Scripts/python -m pip install -r requirements-docs.txt
.venv/Scripts/python -m mkdocs serve
```

Empieza por la [documentación en español](docs/es/index.md) o la [documentación en inglés](docs/en/index.md).

