# Frontend web (Jinja)

La versión web de BankOS se sirve desde el mismo backend FastAPI, con plantillas Jinja2. No tiene un proyecto aparte: las páginas están en `app/web/` y usan los mismos servicios que la API.

## Cómo se ejecuta

Desde la raíz del repositorio:

```powershell
.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

Después abre `http://localhost:8000/`. Si no has iniciado sesión verás la página de bienvenida; para entrar, ve a `http://localhost:8000/login`.

Datos de demostración (ejecuta `scripts/seed_demo` antes si tu base de datos está vacía):

| Campo | Valor |
| --- | --- |
| Entidad | `acme` |
| Correo | `alice@acme.demo` |
| Contraseña | `DemoPass123` |

## Estructura

| Archivo | Qué hace |
| --- | --- |
| `app/web/routes.py` | Rutas de las páginas y los formularios. |
| `app/web/auth.py` | Lectura de la sesión desde la cookie `bankos_session`. |
| `app/web/presentation.py` | Filtros de plantilla: `money`, `datetime_es`, `account_name`, `masked_number`, `transaction_label`. |
| `app/web/templates/base.html` | Diseño común: barra superior, barra lateral desplegable y hoja de estilos. |
| `app/web/templates/landing.html` | Página pública de bienvenida. |
| `app/web/templates/login.html` | Inicio de sesión en dos paneles. |
| `app/web/templates/dashboard.html` | Panel con productos, operaciones rápidas y movimientos. |
| `app/web/static/` | Imágenes de fondo. |

## Páginas

| Ruta | Acceso | Descripción |
| --- | --- | --- |
| `/` | Público si no hay sesión | Landing. Con sesión muestra el panel. |
| `/login` | Público | Formulario de acceso. |
| `/deposit`, `/withdraw` | Cliente | Depósito y retiro desde una cuenta propia. |
| `/transfer` | Cliente | Calcula la comisión y confirma la transferencia. |
| `/transactions` | Cliente | Historial de movimientos. |
| `/profile` | Cliente | Datos del usuario y de la entidad. |
| `/logout` (POST) | Cliente | Cierra la sesión. |

Las rutas que requieren sesión redirigen a `/login` si no hay una cookie válida.

## Diseño

- Colores: morado de marca `#6A00D4`, morado oscuro `#2A0B55` y fondo lavanda `#F6F2FF`.
- Estilos con Tailwind CSS 2.2.19 y iconos de Font Awesome 6.5.2, ambos desde cdnjs.
- Importante: esta versión de Tailwind no admite valores entre corchetes (por ejemplo `h-[calc(...)]`). Para esos casos se usa `style="..."`.
- La barra lateral se puede contraer con el botón ☰. El estado se guarda en `localStorage` con la clave `bankos-sidebar`.
- Las cuentas se muestran con nombre por moneda ("Cuenta en euros", "Cuenta en dólares") y el número enmascarado (`•••• 5916`), porque el backend no guarda un nombre de cuenta.

## Pruebas

```powershell
.venv\Scripts\python -m pytest tests/test_web.py
.venv\Scripts\python -m ruff check app/web tests/test_web.py
```

## Limitaciones conocidas

- No hay recuperación de contraseña ni registro de clientes: el backend no lo ofrece.
- Los selectores de cuenta en depósito, retiro y transferencia muestran el número completo.
- Las imágenes de fondo son recursos de diseño; la de la landing y la del login se sirven desde `/static/`.
