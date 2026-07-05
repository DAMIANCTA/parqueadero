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

## Integraciones actuales

- `GET /health`
- `POST /parking/entry`
- `POST /parking/exit`

## Configuracion de API

La URL base se configura con `dart-define`:

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8004
```

Valor por defecto:

- Android emulator: `http://10.0.2.2:8004`

## Seguridad actual

- No guarda tokens ni datos sensibles en texto plano.
- La sesion de operador vive solo en memoria.
- Las capturas se usan de forma temporal en el flujo UI; no se persisten en la app.

## Nota

Este repositorio no incluye los directorios de plataforma generados por `flutter create` porque el SDK Flutter no esta disponible en este entorno. El codigo fuente de la app y su estructura quedan preparados para integrarlos en cuanto se genere el proyecto de plataforma.
