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

## Seguridad de dispositivos

- Cada dispositivo movil debe identificarse y autenticarse.
- Los dispositivos IoT deben publicar y consumir solo en topicos autorizados.
- Los comandos de apertura deben ser auditables y firmados en fases posteriores.

## Estado en Fase 1

La arquitectura ya contempla JWT, roles, auditoria, cifrado y separacion de datos, pero la implementacion completa queda para fases siguientes. En esta fase se documenta el modelo de seguridad y se dejan los servicios mock listos para crecer sin rehacer la base.
