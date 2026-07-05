# PostgreSQL Core

Base de datos transaccional principal del sistema.

## Estructura

- `migrations/`: esquema SQL versionado.
- `seeds/`: datos semilla de referencia.
- `init/`: bootstrap para aplicar migraciones y semillas cuando el contenedor se inicializa con un volumen vacio.

## Archivos principales

- `migrations/001_enable_extensions.sql`
- `migrations/002_create_core_schema.sql`
- `migrations/003_create_indexes_and_triggers.sql`
- `seeds/001_seed_reference_data.sql`
