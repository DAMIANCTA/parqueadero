# Contratos API Base

Estos contratos son iniciales y estan pensados para alinear al equipo antes de implementar la logica real. Los servicios de IA estan simulados; sus respuestas sirven para integrar frontend, gateway y flujos operativos sin bloquear el proyecto.

## Archivos

- [api-gateway.yaml](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\api-contracts\api-gateway.yaml)
- [auth-service.yaml](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\api-contracts\auth-service.yaml)
- [identity-service.yaml](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\api-contracts\identity-service.yaml)
- [parking-session-service.yaml](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\api-contracts\parking-session-service.yaml)
- [payment-service.yaml](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\api-contracts\payment-service.yaml)
- [facial-recognition-service.yaml](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\api-contracts\facial-recognition-service.yaml)
- [plate-recognition-service.yaml](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\api-contracts\plate-recognition-service.yaml)
- [liveness-service.yaml](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\api-contracts\liveness-service.yaml)
- [iot-service.yaml](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\api-contracts\iot-service.yaml)
- [media-service.yaml](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\api-contracts\media-service.yaml)

## Convenciones iniciales

- Versionado inicial: `/api/v1`
- Respuesta de salud: `GET /health`
- Identificadores: UUID como objetivo para siguientes fases
- Tiempos: ISO-8601 UTC
- Errores: estructura JSON uniforme en fases posteriores
