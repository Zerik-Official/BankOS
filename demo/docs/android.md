# App móvil (Flutter, Android)

La app está en `mobile/` y usa Flutter con Riverpod (estado), go_router (navegación) y el paquete `http` para hablar con la API.

## Requisitos

- Flutter 3.50 o superior, con el SDK de Android instalado.
- Un emulador Android (por ejemplo `Pixel_7`) o un teléfono con depuración USB.
- El backend en marcha (ver `docs/frontend/web.md`).

## Cómo se ejecuta

Desde `mobile/`:

```powershell
flutter pub get
flutter run -d emulator-5554
```

La URL del backend se toma de `lib/core/config/api_config.dart`:

- En Android (emulador) usa `http://10.0.2.2:8000/api/v1`, que apunta al equipo donde corre el backend.
- Para cambiarla en la compilación: `flutter run --dart-define=API_BASE_URL=http://IP:PUERTO/api/v1`.

Para compilar un APK de depuración:

```powershell
flutter build apk --debug
```

El archivo queda en `build/app/outputs/flutter-apk/app-debug.apk`.

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `lib/app/` | Arranque, tema (`theme.dart`), rutas (`router.dart`) y barra inferior. |
| `lib/core/` | Configuración de la API, errores, formato de dinero y widgets reutilizables. |
| `lib/data/` | Repositorio de la API, modelos y un repositorio de datos de prueba. |
| `lib/features/` | Pantallas: login, inicio, movimientos, depósito, retiro, transferencia, avisos y perfil. |
| `lib/providers/` | Estado con Riverpod: sesión, datos bancarios y avisos. |
| `test/` | Pruebas unitarias y de widgets. |

## Funciones

- **Inicio:** tarjeta de saldo con carrusel por cuenta, con el nombre por moneda y el número enmascarado. Incluye acciones rápidas y los últimos movimientos.
- **Movimientos:** búsqueda y filtros (Todos, Ingresos, Egresos), agrupados por día.
- **Transferencias:** puedes elegir una cuenta propia o escribir el número de otra persona. Para otra persona, la app pide confirmación antes de enviar.
- **Avisos:** la app consulta los movimientos cada 15 segundos. Si llega dinero o sale dinero desde otro canal, aparece un aviso y un contador en la campana. Puedes marcar uno como leído o marcarlos todos.
- **Perfil:** datos del usuario y de la entidad, y cerrar sesión.

## Pruebas

```powershell
flutter test
flutter analyze
```

## Limitaciones conocidas

- Los avisos solo funcionan con la app abierta; no hay notificaciones push.
- Los avisos y su estado de lectura no se guardan al cerrar la app.
- No hay recuperación de contraseña ni registro de clientes: el backend no lo ofrece.
- No hay transferencias entre bancos: cada entidad es independiente.
- En el emulador a veces aparece el aviso "System UI isn't responding". Reiniciar el emulador lo soluciona.
