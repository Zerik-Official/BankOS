# BankOS Mobile

Aplicación Flutter de BankOS. Se conecta a la API del backend (`/api/v1`) para
iniciar sesión, consultar cuentas y movimientos, depositar, retirar y transferir.

## 1. Arrancar el backend

Desde la raíz del repositorio, en tu máquina:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m scripts.seed_demo
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

En Windows (Git Bash o PowerShell), usa `.venv\Scripts\python` y `.venv\Scripts\pip`
en lugar de `.venv/bin/...`.

Antes de arrancar, cambia `JWT_SECRET_KEY` en `.env`. Si ejecutas la app web en un
puerto distinto de 8000, 5173, 5000, 8080 o 9000, añade ese origen a `CORS_ORIGINS`.

## 2. Ejecutar la app

```bash
cd mobile
flutter pub get
```

- **Chrome:** `flutter run -d chrome --web-port 5000`. El puerto 5000 ya está
  permitido en `CORS_ORIGINS` del ejemplo.
- **Emulador de Android:** `flutter run`. La app usa `http://10.0.2.2:8000/api/v1`
  automáticamente, que es la forma de llegar al PC desde el emulador.
- **Otro dispositivo o URL distinta:**
  `flutter run --dart-define=API_BASE_URL=http://192.168.1.20:8000/api/v1`

## 3. Usuarios de demo

Contraseña de todos: `DemoPass123`.

| Entidad | Correo | Rol |
| --- | --- | --- |
| `acme` | `alice@acme.demo` | cliente (la app la rellena por defecto) |
| `acme` | `bob@acme.demo` | cliente |
| `acme` | `admin@acme.demo` | administrador (la app no lo usa) |

Los números de cuenta cambian en cada `seed_demo`; cópialos de la salida del script.

## 4. Pruebas

```bash
flutter analyze
flutter test
```

Las pruebas no necesitan el backend: las de `test/data/api/` usan un cliente HTTP
simulado.

## 5. Estructura

```text
lib/
  app/                 Arranque, rutas (go_router), tema y barra inferior
  core/
    config/            URL de la API
    errors/            Errores de la app y mensajes en español
    format/            Importes (texto con dos decimales)
    widgets/           Widgets reutilizables
  data/
    api/               ApiClient (HTTP, sobre de respuesta) y ApiBankRepository
    bank_repository.dart       Contrato de acceso a datos
    fake_bank_repository.dart  Datos falsos, solo para pruebas
    models/                    Modelos con los nombres de campo del backend
  providers/           Estado con Riverpod (sesión, datos bancarios, repositorio)
  features/            Una carpeta por pantalla
test/                  Utilidades, cliente HTTP, widgets y repositorio falso
```

## 6. Detalles de la integración

- Cada operación de dinero envía una cabecera `Idempotency-Key` con un UUID nuevo.
  Si el servidor rechaza la operación, el registro queda en el historial como
  «rechazado» y no cuenta como dinero movido.
- Los importes llegan como texto con dos decimales (`"898.00"`) y se envían igual.
- El token vive solo en memoria: al cerrar la app hay que volver a iniciar sesión.
- La lista de movimientos incluye transferencias recibidas. El signo se calcula
  comparando los números de cuenta del usuario.
