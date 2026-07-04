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

## Seguridad de dispositivos

- Cada dispositivo movil debe identificarse y autenticarse.
- Los dispositivos IoT deben publicar y consumir solo en topicos autorizados.
- Los comandos de apertura deben ser auditables y firmados en fases posteriores.

## Estado en Fase 1

La arquitectura ya contempla JWT, roles, auditoria, cifrado y separacion de datos, pero la implementacion completa queda para fases siguientes. En esta fase se documenta el modelo de seguridad y se dejan los servicios mock listos para crecer sin rehacer la base.
