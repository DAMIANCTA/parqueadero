# Diseno de Base de Datos

## Enfoque general

El sistema usa dos bases:

- Base principal PostgreSQL para datos transaccionales.
- Base biometrica PostgreSQL separada para embeddings y referencias faciales.

## Base principal

### `universities`

- `id`
- `name`
- `code`
- `status`
- `created_at`

### `campuses`

- `id`
- `university_id`
- `name`
- `code`
- `address`
- `status`

### `gates`

- `id`
- `campus_id`
- `name`
- `code`
- `direction_type`
- `status`

### `people`

- `id`
- `university_id`
- `institutional_code`
- `full_name`
- `document_number`
- `person_type`
- `status`

### `vehicles`

- `id`
- `plate`
- `vehicle_type`
- `color`
- `status`

### `vehicle_authorizations`

- `id`
- `vehicle_id`
- `person_id`
- `permission_type`
- `valid_from`
- `valid_until`
- `status`

### `parking_sessions`

- `id`
- `session_type`
- `vehicle_id`
- `person_id`
- `entry_gate_id`
- `exit_gate_id`
- `entry_time`
- `exit_time`
- `status`

### `session_events`

- `id`
- `parking_session_id`
- `event_type`
- `gate_id`
- `device_id`
- `result`
- `created_at`

### `payments`

- `id`
- `parking_session_id`
- `amount`
- `currency`
- `payment_status`
- `payment_method`
- `paid_at`

### `media_assets`

- `id`
- `parking_session_id`
- `asset_type`
- `object_path`
- `bucket_name`
- `created_at`

### `audit_logs`

- `id`
- `actor_id`
- `actor_role`
- `action`
- `resource_type`
- `resource_id`
- `metadata`
- `created_at`

## Base biometrica

### `biometric_profiles`

- `id`
- `person_id`
- `profile_status`
- `created_at`

### `face_embeddings`

- `id`
- `biometric_profile_id`
- `embedding_vector`
- `source_asset_id`
- `quality_score`
- `created_at`

### `face_verification_events`

- `id`
- `person_id`
- `parking_session_id`
- `similarity_score`
- `liveness_score`
- `result`
- `created_at`

## Notas de Fase 1

- No hay migraciones reales todavia.
- El diseño sirve como contrato de dominio inicial.
- `pgvector` queda previsto para `face_embeddings`.
- Los servicios mock usan este diseño como referencia, no como implementacion final.
