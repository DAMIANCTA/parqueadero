# Arquitectura General

## Vision

Smart Parking University es una plataforma mobile-first para controlar accesos a parqueaderos universitarios en multiples universidades, campus y puertas. Cada puerta usa un dispositivo movil para capturar rostro y placa, consultar al backend y autorizar o rechazar la apertura de la barrera.

## Capas principales

### 1. Mobile

- App Flutter para operadores de puerta.
- Captura de imagenes de rostro y placa.
- Envio de eventos de entrada y salida.
- Visualizacion inmediata del resultado de validacion.

### 2. Backend de microservicios

- `api_gateway`: entrada unica para clientes.
- `auth_service`: autenticacion y autorizacion.
- `identity_service`: personas, placas, roles y permisos.
- `parking_session_service`: sesiones de ingreso y salida.
- `payment_service`: estado de pago para visitantes.
- `media_service`: referencia a imagenes en almacenamiento.
- `iot_service`: publicacion de eventos de barrera.
- `facial_recognition_service`: mock preparado para reconocimiento facial.
- `plate_recognition_service`: mock preparado para lectura de placas.
- `liveness_service`: mock preparado para deteccion de vida.

### 3. Datos y almacenamiento

- PostgreSQL principal para el dominio transaccional.
- PostgreSQL biometrico separado para embeddings y datos sensibles.
- MinIO para imagenes y evidencia.

### 4. IoT e integracion fisica

- Mosquitto como broker MQTT.
- Node-RED para flujos de integracion y pruebas.
- ThingsBoard como opcion futura de observabilidad IoT.
- ESP32 para control de barreras y perifericos en una fase posterior.

## Principios de arquitectura

- Multiuniversidad y multicampus desde el modelo de dominio.
- Microservicios desacoplados.
- Separacion de datos sensibles y biometricos.
- Mobile-first para operacion en puerta.
- Uso de mocks en Fase 1 para no bloquear integracion temprana.
- Evolucion incremental hacia IA real, auditoria completa y control fisico.

## Flujo de alto nivel

1. El operador usa la app movil en una puerta.
2. La app envia capturas y metadatos al backend.
3. El backend consulta servicios mock de placa, rostro y liveness.
4. Se valida identidad, placa, permisos, sesion y pago segun el tipo de usuario.
5. Si la validacion es correcta, `iot_service` publica un evento para abrir la barrera.
6. Node-RED y, mas adelante, ESP32 ejecutan la accion fisica.

## Estado de Fase 1

En esta fase no hay biometria real ni OCR real. Los servicios relacionados existen para que frontend, contratos API e integracion IoT puedan avanzar con respuestas simuladas.
