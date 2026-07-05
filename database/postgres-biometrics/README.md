# PostgreSQL Biometrics

Base de datos biometrica separada del dominio transaccional principal.

## Objetivo

Almacenar plantillas faciales, evidencia de imagen referenciada en MinIO y logs de acceso biometrico sin mezclar estos datos con la base operativa principal.

## Estructura

- `migrations/`: esquema SQL versionado para biometria.
- `init/`: bootstrap para aplicar migraciones automaticamente al inicializar un volumen vacio.

## Consideraciones

- No se guardan fotos binarias en PostgreSQL.
- Las imagenes se referencian por bucket y ruta de MinIO.
- Se almacena hash `SHA-256` para integridad.
- `pgvector` queda habilitado para `embedding_vector`.
- `person_id` y `university_id` son referencias logicas al dominio principal, no llaves foraneas cruzadas entre bases.
