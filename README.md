# Smart Parking University

Repositorio inicial del sistema Smart Parking University: una plataforma mobile-first, multiuniversidad y basada en microservicios para controlar accesos de parqueaderos en universidades, campus y puertas distribuidas.

En esta Fase 1 dejamos la base del proyecto lista para evolucionar por etapas: estructura del repositorio, servicios backend mock con FastAPI, documentacion funcional, archivos de entorno y `docker-compose` con la infraestructura principal. Todavia no hay reconocimiento facial real ni lectura real de placas; esos componentes quedan preparados como mocks.

La Fase 4 reorganiza el backend en microservicios dedicados con estructura limpia por servicio y endpoints mock uniformes.

## Objetivo del sistema

El sistema debe permitir que un vehiculo entre por una puerta y salga por otra, validando placa, rostro, permisos, sesion de parqueo, pago y reglas operativas antes de abrir la barrera.

El producto esta pensado para dos flujos:

- Visitantes: crean una sesion temporal al ingresar y deben validar rostro, placa y pago al salir.
- Estudiantes, docentes y trabajadores: usan placas previamente autorizadas y su rostro debe coincidir con una persona habilitada para ese vehiculo.

## Estructura inicial del repositorio

```text
parqueadero/
|-- backend/
|   |-- services/
|   |   |-- api-gateway/
|   |   |-- auth-service/
|   |   |-- university-service/
|   |   |-- vehicle-service/
|   |   |-- parking-service/
|   |   |-- face-service/
|   |   |-- plate-service/
|   |   |-- payment-service/
|   |   |-- iot-service/
|   |   |-- audit-service/
|   |   `-- shared/
|   `-- README.md
|-- mobile/
|   |-- app/
|   `-- README.md
|-- iot/
|   |-- mqtt/
|   |-- nodered/
|   |-- thingsboard/
|   |-- esp32/
|   `-- README.md
|-- database/
|   |-- postgres-core/
|   |-- postgres-biometrics/
|   |-- schemas/
|   `-- README.md
|-- storage/
|   |-- minio/
|   `-- README.md
|-- docs/
|   |-- architecture.md
|   |-- mobile-flow.md
|   |-- security.md
|   |-- database-design.md
|   `-- iot-flow.md
|-- scripts/
|-- .env.example
`-- docker-compose.yml
```

## Que incluye esta fase

- Backend preparado con microservicios mock en FastAPI.
- Estructura base para app movil Flutter.
- Base para integracion IoT con MQTT, Node-RED, ThingsBoard y ESP32.
- Diseño inicial de bases de datos principal y biometrica.
- Almacenamiento previsto con MinIO.
- Documentacion inicial para desarrollo y exposicion.

## Infraestructura prevista

- PostgreSQL principal para datos transaccionales.
- PostgreSQL biometrico separado para embeddings y metadata sensible.
- MinIO para imagenes y evidencia operativa.
- Mosquitto como broker MQTT.
- Node-RED para maquetado e integracion rapida.
- ThingsBoard como integracion opcional futura.

## Puesta en marcha

### Prerrequisitos

- Docker Desktop iniciado
- Docker Compose disponible
- Puertos `5432`, `5433`, `8000-8009`, `1880`, `1883`, `9000`, `9001` y `9002` libres

### Arranque rapido

```powershell
.\scripts\dev-up.ps1
```

### Arranque manual

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## Documentacion principal

- [Arquitectura general](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\architecture.md)
- [Flujo mobile de entrada y salida](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\mobile-flow.md)
- [Seguridad y proteccion de datos](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\security.md)
- [Diseño de base de datos](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\database-design.md)
- [Flujo IoT](C:\Users\damia\OneDrive\Documentos\parqueadero\docs\iot-flow.md)

## Estado de los mocks

- `face-service`: devuelve una verificacion facial simulada.
- `plate-service`: devuelve una deteccion de placa simulada.
- `parking-service`: devuelve una sesion simulada.
- `payment-service`: permite buscar sesiones, calcular tarifa y registrar pagos simulados.
- `iot-service`: simula la publicacion de comando de apertura.
- `api-gateway`: expone un catalogo mock de servicios disponibles.

## Siguiente paso recomendado

La siguiente fase natural es modelar dominio real y persistencia: universidades, campus, puertas, personas, placas autorizadas, sesiones, pagos y auditoria.
