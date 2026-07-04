# Microservicios Base

## api_gateway

Responsabilidad: punto de entrada para app movil y futuros clientes. En fases posteriores concentrara autenticacion, versionado, rate limiting, agregacion y observabilidad.

## auth_service

Responsabilidad: autenticacion, emision de JWT, roles, permisos y politicas de acceso.

## identity_service

Responsabilidad: universidades, campus, puertas, personas, roles institucionales, placas autorizadas y vigencias.

## parking_session_service

Responsabilidad: sesiones de parqueo, eventos de entrada/salida, reglas de permanencia y validaciones de acceso operativo.

## payment_service

Responsabilidad: consulta de estado de pago, reglas tarifarias futuras y conciliacion de pagos de visitantes.

## facial_recognition_service

Responsabilidad: verificacion facial y gestion de embeddings. En esta fase opera en modo mock.

## plate_recognition_service

Responsabilidad: deteccion y lectura de placa a partir de imagen. En esta fase opera en modo mock.

## liveness_service

Responsabilidad: deteccion de vida para evitar fraude por foto o video. En esta fase opera en modo mock.

## media_service

Responsabilidad: carga, referencia y eventual ciclo de vida de imagenes almacenadas en MinIO.

## iot_service

Responsabilidad: publicar eventos operativos hacia MQTT, Node-RED y futuros controladores ESP32.

## Separacion de datos

- Datos transaccionales: PostgreSQL principal.
- Datos biometricos: PostgreSQL biometrico con `pgvector`.
- Evidencia visual: MinIO.
- Eventos de dispositivo y barrera: MQTT.

## Estrategia de integracion

- HTTP interno entre microservicios para fase inicial.
- MQTT para eventos de apertura/cierre/telemetria de dispositivos.
- Node-RED como maqueta de integracion e instrumentacion rapida.
- ThingsBoard queda como opcion para una fase posterior.
