# Arquitectura General

## Vision del sistema

El sistema administra el acceso a parqueaderos universitarios en varias universidades, multiples campus y varias puertas por campus. Cada puerta opera con un dispositivo movil que captura rostro y placa, consulta al backend y solo abre la barrera cuando la validacion completa es satisfactoria.

## Principios de diseno

- Mobile-first: la operacion primaria ocurre desde dispositivos Android/iOS.
- Multiuniversidad: una misma plataforma administra varias instituciones.
- Multi-campus y multipuerta: cada campus tiene varias puertas con reglas propias.
- Microservicios: responsabilidades separadas, despliegue desacoplado.
- Zero trust operativo: ninguna barrera se abre sin validacion explicita.
- Datos sensibles aislados: biometria, medios e identidad separados.
- Faseable: primero mocks y contratos; despues integraciones reales.

## Componentes principales

### Clientes

- App movil Flutter para guardias u operadores en puerta.
- Futuro panel web administrativo.
- Futuro panel de monitoreo y auditoria.

### Servicios de negocio

- `api_gateway`
- `auth_service`
- `identity_service`
- `parking_session_service`
- `payment_service`
- `media_service`
- `iot_service`

### Servicios de IA simulados por ahora

- `facial_recognition_service`
- `plate_recognition_service`
- `liveness_service`

## Bases de datos y almacenamiento

- PostgreSQL principal: universidades, campus, puertas, personas, vehiculos, permisos, sesiones, pagos, auditoria.
- PostgreSQL biometrico con `pgvector`: embeddings faciales y referencias biometrico-operativas.
- MinIO: fotos de rostro, placa, capturas de entrada/salida y evidencia operativa.

## Flujo resumido de visitante

1. La app captura rostro y placa en una puerta de entrada.
2. `plate_recognition_service` retorna una placa detectada mock.
3. `liveness_service` valida prueba de vida mock.
4. `facial_recognition_service` genera o compara referencia mock.
5. `parking_session_service` crea sesion temporal.
6. `media_service` registra imagenes en MinIO.
7. `iot_service` publica evento de apertura de barrera.

Salida:

1. Se captura nuevamente rostro y placa.
2. Se valida coincidencia con la sesion de entrada.
3. `payment_service` confirma pago.
4. `parking_session_service` aprueba salida.
5. `iot_service` ordena apertura.

## Flujo resumido de comunidad universitaria

1. Se captura rostro y placa.
2. `identity_service` valida que la placa exista.
3. `identity_service` valida que el rostro pertenezca a una persona autorizada para esa placa.
4. Se revisa vigencia de permisos.
5. `parking_session_service` registra entrada o salida.
6. `iot_service` abre barrera si procede.

## Alcance de esta fase

Esta fase no implementa:

- Reconocimiento facial real.
- OCR real de placas.
- Antispoofing real.
- Persistencia completa.
- JWT real con llaves y refresh tokens.
- Reglas operativas avanzadas por universidad/campus.

Si deja preparado el terreno para esas fases sin rehacer la arquitectura.
