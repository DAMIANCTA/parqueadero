# Diseno de Base de Datos

## Enfoque general

El sistema mantiene dos bases separadas:

- PostgreSQL principal para el dominio transaccional y operativo.
- PostgreSQL biometrico para embeddings, referencias faciales y datos altamente sensibles.

En Fase 2 ya existe una implementacion SQL real del core principal en:

- [database/postgres-core/migrations/001_enable_extensions.sql](C:\Users\damia\OneDrive\Documentos\parqueadero\database\postgres-core\migrations\001_enable_extensions.sql)
- [database/postgres-core/migrations/002_create_core_schema.sql](C:\Users\damia\OneDrive\Documentos\parqueadero\database\postgres-core\migrations\002_create_core_schema.sql)
- [database/postgres-core/migrations/003_create_indexes_and_triggers.sql](C:\Users\damia\OneDrive\Documentos\parqueadero\database\postgres-core\migrations\003_create_indexes_and_triggers.sql)
- [database/postgres-core/seeds/001_seed_reference_data.sql](C:\Users\damia\OneDrive\Documentos\parqueadero\database\postgres-core\seeds\001_seed_reference_data.sql)

## Convenciones implementadas

- Claves primarias UUID con `gen_random_uuid()`.
- `created_at` y `updated_at` en todas las tablas principales.
- Columna `status` con soporte `active` o `inactive`.
- `university_id` en las tablas donde la particion multiuniversidad aplica.
- Triggers para mantener `updated_at`.
- Indices en llaves foraneas y columnas operativas frecuentes.

## Tablas del core principal

### `universities`

Universidades administradas por la plataforma.

Campos clave:

- `id`
- `name`
- `code`
- `legal_name`
- `country_code`
- `status`

### `campuses`

Campus pertenecientes a una universidad.

Relacion:

- `campuses.university_id -> universities.id`

Campos clave:

- `id`
- `university_id`
- `name`
- `code`
- `address_line`
- `city`
- `status`

### `gates`

Puertas de acceso del campus.

Relaciones:

- `gates.university_id -> universities.id`
- `gates.campus_id -> campuses.id`

Campos clave:

- `id`
- `university_id`
- `campus_id`
- `name`
- `code`
- `direction_type`
- `status`

### `devices`

Dispositivos moviles o controladores asociados a una puerta.

Relaciones:

- `devices.university_id -> universities.id`
- `devices.campus_id -> campuses.id`
- `devices.gate_id -> gates.id`

Campos clave:

- `id`
- `university_id`
- `campus_id`
- `gate_id`
- `device_code`
- `device_name`
- `platform`
- `device_type`
- `last_seen_at`
- `status`

### `roles`

Catalogo base de roles de plataforma y operacion.

Campos clave:

- `id`
- `role_key`
- `display_name`
- `description`
- `status`

### `users`

Usuarios del sistema autenticados por backend.

Relaciones:

- `users.university_id -> universities.id`
- `users.role_id -> roles.id`

Campos clave:

- `id`
- `university_id`
- `role_id`
- `username`
- `email`
- `password_hash`
- `first_name`
- `last_name`
- `last_login_at`
- `status`

### `persons`

Representa a estudiantes, docentes, empleados, visitantes u otros actores del dominio.

Relaciones:

- `persons.university_id -> universities.id`
- `persons.user_id -> users.id`
- `persons.campus_id -> campuses.id`

Campos clave:

- `id`
- `university_id`
- `user_id`
- `campus_id`
- `institutional_code`
- `full_name`
- `document_number`
- `email`
- `phone`
- `person_type`
- `status`

### `vehicles`

Vehiculos conocidos por universidad.

Relaciones:

- `vehicles.university_id -> universities.id`
- `vehicles.owner_person_id -> persons.id`

Campos clave:

- `id`
- `university_id`
- `owner_person_id`
- `plate`
- `vehicle_type`
- `brand`
- `model`
- `color`
- `status`

### `vehicle_authorizations`

Define que personas estan autorizadas a usar una placa.

Relaciones:

- `vehicle_authorizations.university_id -> universities.id`
- `vehicle_authorizations.vehicle_id -> vehicles.id`
- `vehicle_authorizations.person_id -> persons.id`

Campos clave:

- `id`
- `university_id`
- `vehicle_id`
- `person_id`
- `authorization_type`
- `valid_from`
- `valid_until`
- `notes`
- `status`

### `parking_sessions`

Sesion de parqueo abierta o cerrada para visitantes o usuarios internos.

Relaciones:

- `parking_sessions.university_id -> universities.id`
- `parking_sessions.campus_id -> campuses.id`
- `parking_sessions.vehicle_id -> vehicles.id`
- `parking_sessions.person_id -> persons.id`
- `parking_sessions.entry_gate_id -> gates.id`
- `parking_sessions.exit_gate_id -> gates.id`
- `parking_sessions.entry_device_id -> devices.id`
- `parking_sessions.exit_device_id -> devices.id`

Campos clave:

- `id`
- `university_id`
- `campus_id`
- `vehicle_id`
- `person_id`
- `entry_gate_id`
- `exit_gate_id`
- `entry_device_id`
- `exit_device_id`
- `session_type`
- `session_status`
- `detected_plate`
- `payment_required`
- `payment_status`
- `entry_time`
- `exit_time`
- `status`

### `payments`

Pagos asociados a sesiones de parqueo.

Relaciones:

- `payments.university_id -> universities.id`
- `payments.parking_session_id -> parking_sessions.id`
- `payments.collected_by_user_id -> users.id`

Campos clave:

- `id`
- `university_id`
- `parking_session_id`
- `collected_by_user_id`
- `reference_code`
- `amount`
- `currency`
- `payment_method`
- `payment_status`
- `paid_at`
- `status`

### `access_events`

Bitacora operativa de intentos, aprobaciones y rechazos de acceso.

Relaciones:

- `access_events.university_id -> universities.id`
- `access_events.parking_session_id -> parking_sessions.id`
- `access_events.gate_id -> gates.id`
- `access_events.device_id -> devices.id`
- `access_events.person_id -> persons.id`
- `access_events.vehicle_id -> vehicles.id`
- `access_events.operator_user_id -> users.id`

Campos clave:

- `id`
- `university_id`
- `parking_session_id`
- `gate_id`
- `device_id`
- `person_id`
- `vehicle_id`
- `operator_user_id`
- `event_type`
- `result`
- `reason`
- `occurred_at`
- `status`

### `incidents`

Incidentes operativos o de seguridad relacionados con accesos y sesiones.

Relaciones:

- `incidents.university_id -> universities.id`
- `incidents.campus_id -> campuses.id`
- `incidents.gate_id -> gates.id`
- `incidents.parking_session_id -> parking_sessions.id`
- `incidents.reported_by_user_id -> users.id`

Campos clave:

- `id`
- `university_id`
- `campus_id`
- `gate_id`
- `parking_session_id`
- `reported_by_user_id`
- `incident_type`
- `severity`
- `incident_status`
- `description`
- `resolution_notes`
- `resolved_at`
- `status`

### `audit_logs`

Auditoria transversal del sistema para cambios administrativos y acciones sensibles.

Relaciones:

- `audit_logs.university_id -> universities.id`
- `audit_logs.actor_user_id -> users.id`

Campos clave:

- `id`
- `university_id`
- `actor_user_id`
- `actor_role_key`
- `action`
- `resource_type`
- `resource_id`
- `metadata`
- `ip_address`
- `status`

## Datos semilla incluidos

El seed inicial crea:

- Una universidad de prueba.
- Un campus principal.
- Dos puertas: `Puerta Norte` y `Puerta Sur`.
- Roles base:
  - `superadmin`
  - `admin_university`
  - `security`
  - `cashier`
  - `gate_operator`
  - `student`
  - `teacher`
  - `employee`
  - `visitor`
  - `auditor`

## Base biometrica

La base biometrica sigue separada por diseño y se implementara en una fase posterior. El modelo actual del core ya deja listas las referencias necesarias para enlazar sesiones, personas y eventos con futuros servicios biometricos.
