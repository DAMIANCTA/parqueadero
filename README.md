# Sistema Inteligente de Parqueaderos Universitarios

Base inicial de un sistema mobile-first, multiuniversidad y orientado a microservicios para controlar ingresos y salidas de parqueaderos universitarios.

Esta primera fase deja listo el esqueleto del repositorio, la arquitectura inicial, contratos API mock, documentacion y un entorno local con Docker Compose. Todavia no incluye logica real de IA; los servicios de reconocimiento facial, placas y liveness responden con comportamiento simulado para acelerar el desarrollo por fases.

## Objetivos de esta fase

- Definir una estructura de monorepo clara y escalable.
- Separar responsabilidades por microservicio.
- Preparar documentacion para exposicion universitaria.
- Levantar un entorno local ejecutable con FastAPI, PostgreSQL, MinIO, MQTT y Node-RED.
- Dejar contratos base para entrada, salida, validacion biometrica, pagos e IoT.

## Estructura propuesta del repositorio

```text
parqueadero/
|-- apps/
|   `-- mobile_app/
|-- docs/
|   |-- api-contracts/
|   |-- architecture/
|   |-- diagrams/
|   `-- phases/
|-- infra/
|   |-- docker/
|   |-- mqtt/
|   `-- nodered/
|-- scripts/
|-- services/
|   |-- api_gateway/
|   |-- auth_service/
|   |-- facial_recognition_service/
|   |-- identity_service/
|   |-- iot_service/
|   |-- liveness_service/
|   |-- media_service/
|   |-- parking_session_service/
|   |-- payment_service/
|   |-- plate_recognition_service/
|   `-- shared/
|-- .env.example
`-- docker-compose.yml
```

## Microservicios incluidos

- `api_gateway`: punto de entrada HTTP para cliente movil y futuros paneles.
- `auth_service`: autenticacion, JWT, roles y permisos.
- `identity_service`: personas, afiliaciones, placas autorizadas y vigencias.
- `parking_session_service`: sesiones de entrada/salida y reglas operativas.
- `payment_service`: validacion de pagos de visitantes.
- `facial_recognition_service`: verificacion facial mock.
- `plate_recognition_service`: lectura de placas mock.
- `liveness_service`: validacion antispoofing mock.
- `media_service`: carga y referencia de imagenes en MinIO.
- `iot_service`: publicacion de eventos y apertura de barreras por MQTT.

## Infraestructura incluida

- `postgres-core`: base principal transaccional.
- `postgres-biometrics`: base aislada para biometria y `pgvector`.
- `minio`: almacenamiento de imagenes.
- `mosquitto`: broker MQTT para dispositivos y barreras.
- `nodered`: maquetado de flujos IoT e integracion.

## Estado actual

- Backend base en FastAPI por servicio.
- Servicios de IA simulados.
- Contratos API iniciales en `docs/api-contracts/`.
- Compose listo para orquestar contenedores locales.
- Carpeta de app Flutter preparada, sin implementacion aun.

## Puesta en marcha

### Prerrequisitos

- Docker Desktop iniciado
- Docker Compose disponible
- Puerto 5432, 5433, 8000-8009, 9000-9002 y 1880 libres

### Arranque rapido

```powershell
.\scripts\dev-up.ps1
```

### Arranque manual

1. Copiar variables de entorno:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Levantar el entorno:

   ```powershell
   docker compose up --build
   ```

3. Probar salud de servicios:

   - Gateway: `http://localhost:8000/health`
   - Auth: `http://localhost:8001/health`
   - Identity: `http://localhost:8002/health`
   - Parking Sessions: `http://localhost:8003/health`
   - Payment: `http://localhost:8004/health`
   - Face: `http://localhost:8005/health`
   - Plate: `http://localhost:8006/health`
   - Liveness: `http://localhost:8007/health`
   - IoT: `http://localhost:8008/health`
   - Media: `http://localhost:8009/health`
   - Node-RED: `http://localhost:1880`
   - MinIO Console: `http://localhost:9001`

## Documentacion

- Arquitectura general: [docs/architecture/overview.md](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\architecture\overview.md)
- Descripcion de microservicios: [docs/architecture/microservices.md](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\architecture\microservices.md)
- Diagramas: [docs/diagrams/system-context.md](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\diagrams\system-context.md)
- Contratos API: [docs/api-contracts/README.md](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\api-contracts\README.md)
- Alcance de la fase 1: [docs/phases/phase-01-foundation.md](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\phases\phase-01-foundation.md)

## Siguientes fases sugeridas

1. Scaffold real de la app Flutter y flujos de captura.
2. Persistencia real en PostgreSQL y pgvector.
3. Gateway con orquestacion entre servicios.
4. Seguridad completa con JWT, RBAC y auditoria.
5. Integracion real con ESP32, MQTT y barreras.
6. IA real para rostro, placa y liveness.
