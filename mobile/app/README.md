# Smart Parking University Mobile

Base Flutter mobile-first para operacion en puertas de acceso.

## Pantallas incluidas

1. Login
2. Seleccion de universidad, campus y puerta
3. Modo entrada
4. Modo salida
5. Captura de rostro
6. Captura de placa
7. Resultado de autorizacion
8. Historial basico
9. Demo IoT

## Integraciones actuales

- `GET /health`
- `POST /parking/entry`
- `POST /parking/exit`
- `POST /demo/open-gate`

## Configuracion de API

La URL base se configura con `dart-define`:

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Valor por defecto:

- Android emulator: `http://10.0.2.2:8000`
- Windows local: `http://localhost:8000`

## Seguridad actual

- No guarda tokens ni datos sensibles en texto plano.
- La sesion de operador vive solo en memoria.
- Las capturas se usan de forma temporal en el flujo UI; no se persisten en la app.

## Nota

La app ya puede ejecutarse en Windows y en Android apuntando al `api-gateway`. Para pruebas locales se recomienda usar el comando documentado en [docs/testing-local.md](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\testing-local.md).
