# Seguridad

## Principios

- Menor privilegio.
- Separacion de responsabilidades.
- Proteccion reforzada para datos biometricos.
- Trazabilidad completa de acciones operativas.
- Cifrado en transito y en reposo.

## Roles base

- `super_admin`: administra toda la plataforma multiuniversidad.
- `university_admin`: administra una universidad especifica.
- `campus_admin`: administra campus, puertas y configuraciones locales.
- `gate_operator`: opera ingreso y salida desde dispositivos moviles.
- `security_auditor`: consulta logs, eventos y auditoria.
- `billing_operator`: consulta y valida pagos.

## Autenticacion y autorizacion

- JWT para autenticacion de clientes.
- Roles y permisos por servicio.
- Futuro soporte para refresh tokens y rotacion de llaves.
- Validacion por ambito: universidad, campus y puerta.

## Proteccion de datos

- Datos personales y datos biometricos en repositorios separados.
- Minimizacion de datos en respuestas de APIs.
- Uso de IDs internos en vez de exponer informacion sensible innecesaria.
- Politicas de retencion para imagenes y evidencia.
- Validacion de liveness antes de enviar biometria a flujos de autorizacion.

## Cifrado

- TLS para trafico entre cliente y backend.
- TLS interno recomendado entre servicios en ambientes productivos.
- Cifrado en reposo para discos, backups y snapshots.
- Secretos fuera del codigo fuente en entornos reales.

## Auditoria

- Registro de accesos a APIs.
- Registro de aperturas de barrera.
- Registro de cambios de permisos, placas y usuarios.
- Registro de acciones administrativas y de operadores.
- Timestamps, actor, dispositivo, puerta, universidad y resultado de validacion.

## Separacion biometrica

- Base de datos principal: dominio transaccional.
- Base biometrica: embeddings, referencias faciales y metadatos estrictamente necesarios.
- Almacenamiento de imagenes en MinIO con acceso controlado.
- Acceso a biometria solo desde servicios autorizados.

## Por que la biometria esta separada

- Reduce el impacto de una filtracion: un incidente en la base operativa no expone automaticamente plantillas faciales.
- Permite controles de acceso mas estrictos: menos servicios y menos personas necesitan llegar a la base biometrica.
- Facilita politicas de retencion distintas: la biometria y la evidencia visual suelen tener reglas legales y operativas diferentes a las tablas transaccionales.
- Mejora el cumplimiento y la auditoria: es mas facil demostrar que los datos sensibles viven en un perimetro separado.
- Evita acoplar imagenes y embeddings con operaciones comunes: la mayoria de consultas de negocio no necesitan tocar datos biometricos.
- Permite cifrado, respaldo y rotacion de credenciales dedicados para la capa mas sensible.

## Implementacion actual de la base biometrica

- `face_templates`: plantillas faciales con `embedding_vector`, `model_name`, `quality_score`, `encrypted`, `expires_at` y `status`.
- `image_evidence`: referencias a MinIO, hash `SHA-256`, tipo de imagen, expiracion y estado.
- `biometric_access_logs`: bitacora de verificaciones biometricas y decisiones de acceso.
- Las imagenes no se guardan dentro de PostgreSQL; solo se almacena su referencia segura y metadatos de integridad.

## Flujo actual de `face-service`

- `POST /faces/enroll` registra una referencia de imagen en MinIO, genera embedding y deja la plantilla en la base biometrica.
- `POST /faces/verify` compara una imagen de prueba contra una plantilla enrolada usando similitud configurable.
- `POST /faces/compare` compara dos referencias de imagen sin tocar la base principal.
- `POST /faces/liveness-check` registra score y decision de prueba de vida en la bitacora biometrica.
- En todos los casos el contrato trabaja con referencias a MinIO y metadatos biometricos; no con fotos persistidas en la base transaccional principal.

## Liveness y proteccion anti-spoofing

- La app movil ejecuta un reto dinamico antes de enviar la solicitud de acceso.
- Los retos iniciales son: mirar a la izquierda, mirar a la derecha y parpadear.
- El resultado genera `liveness_score`; si el score es bajo, la validacion se bloquea en dispositivo y no se envia la operacion al backend.
- Este control reduce el riesgo de fraude con fotos impresas, videos pregrabados o pantallas mostrando el rostro del titular.
- En esta fase el calculo es mock, pero la interfaz ya esta preparada para motores reales como TensorFlow Lite, MediaPipe o ML Kit.

## Manejo de datos de liveness en dispositivo

- La fase actual trabaja con captura simulada de varios frames para no introducir todavia un modelo de IA definitivo.
- El flujo conserva solo el `face_image_id`, `liveness_score` y metadatos minimos necesarios para la solicitud.
- No se plantea guardar video crudo de liveness en almacenamiento persistente del dispositivo.
- Cuando se integre el modelo real, la recomendacion es procesar en memoria o en almacenamiento temporal cifrado y eliminar frames locales al terminar cada intento.
- Los resultados de liveness deben entrar tambien al circuito de auditoria para dejar evidencia de aprobacion o rechazo.

## Seguridad de dispositivos

- Cada dispositivo movil debe identificarse y autenticarse.
- Los dispositivos IoT deben publicar y consumir solo en topicos autorizados.
- Los comandos de apertura deben ser auditables y firmados en fases posteriores.
- Los modulos de liveness y captura facial deben usar solo camara frontal y pedir reintento cuando la calidad o el score sean insuficientes.

## Estado en Fase 1

La arquitectura ya contempla JWT, roles, auditoria, cifrado y separacion de datos, pero la implementacion completa queda para fases siguientes. En esta fase se documenta el modelo de seguridad y se dejan los servicios mock listos para crecer sin rehacer la base.
