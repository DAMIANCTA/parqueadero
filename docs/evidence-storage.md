# Almacenamiento de Evidencias en MinIO

## Objetivo

Este documento describe el flujo de almacenamiento de evidencias para Smart Parking University usando MinIO como repositorio privado de objetos.

La fase actual trabaja en modo mock o mixto:

- la app puede enviar imagenes reales seleccionadas o capturadas;
- tambien puede generar archivos mock para demostracion;
- el backend guarda la evidencia en MinIO y conserva en PostgreSQL biometrico solo la referencia del archivo y sus metadatos.

## Buckets utilizados

El backend prepara y usa los siguientes buckets:

- `parking-faces`
- `parking-plates`
- `parking-evidence`
- `parking-temp`

En la fase actual:

- `face_entry` y `face_exit` se almacenan en `parking-faces`
- `plate_entry` y `plate_exit` se almacenan en `parking-plates`

Los buckets se crean automaticamente si no existen. No se publica ningun bucket ni se configura acceso anonimo.

## Por que las fotos estan en MinIO

Las imagenes no se almacenan dentro de PostgreSQL porque:

- son archivos binarios y crecen mucho mas rapido que los datos transaccionales;
- MinIO permite organizar, retener y mover objetos de forma mas eficiente;
- simplifica futuras politicas de expiracion, archivado y replicacion;
- reduce el impacto de rendimiento sobre las consultas operativas del sistema.

## Por que la base guarda solo referencias

La base de datos guarda metadatos y referencias porque:

- conserva trazabilidad sin duplicar binarios;
- facilita auditoria y consulta por `session_id`, `plate` o `image_type`;
- permite aplicar controles distintos sobre objetos y datos relacionales;
- prepara el sistema para cifrado, expiracion y firmas temporales sin exponer buckets.

## Endpoint principal

El acceso recomendado desde la app se hace siempre a traves del `api-gateway`.

### `POST /evidence/upload`

Endpoint expuesto por:

- Gateway: `POST /evidence/upload`
- Servicio interno final: `parking-service -> /evidence/upload`

### Campos esperados

Se envian como `multipart/form-data`:

- `file`
- `image_type`
- `plate`
- `session_id` opcional

### Tipos de imagen soportados

- `face_entry`
- `face_exit`
- `plate_entry`
- `plate_exit`

### Respuesta

```json
{
  "image_id": "d1ecb1d2-6a46-4a6f-9490-f6d831f2f2aa",
  "bucket": "parking-faces",
  "object_name": "2026/07/06/face_entry/VIS1001-a1b2c3d4e5f6-face-entry-VIS1001.txt",
  "image_type": "face_entry",
  "session_id": null,
  "plate": "VIS1001",
  "hash_sha256": "9f1d7d5c8f6f3b1a7f6c3a29a66d5e4a7d6f8a9b0c1d2e3f4a5b6c7d8e9f0a1b",
  "encrypted": true,
  "created_at": "2026-07-06T12:20:00Z",
  "expires_at": null,
  "status": "active"
}
```

## Flujo de entrada

1. La app prepara dos evidencias:
   - rostro de entrada
   - placa de entrada
2. Cada evidencia se envia a `POST /evidence/upload`.
3. El backend sube el archivo a MinIO y responde con `image_id`.
4. La app llama a `POST /parking/entry` enviando:
   - `face_image_id` con la referencia almacenada del rostro
   - `plate_image_id` con la referencia almacenada de la placa
   - `face_mock_id` para validacion facial mock
5. `parking-service` crea la sesion y enlaza esas evidencias con el `session_id`.

## Flujo de salida

1. La app prepara dos evidencias:
   - rostro de salida
   - placa de salida
2. Cada evidencia se envia a `POST /evidence/upload`.
3. La app llama a `POST /parking/exit` con:
   - `face_image_id`
   - `plate_image_id`
   - `face_mock_id`
4. `parking-service` enlaza las referencias a la sesion activa o al registro mock de salida.

## Datos conservados por referencia

Cada evidencia conserva:

- `image_id`
- `session_id`
- `bucket`
- `object_name`
- `image_type`
- `plate`
- `hash_sha256`
- `encrypted`
- `created_at`
- `expires_at`
- `status`

En esta fase no se expone una descarga publica ni URL firmada de lectura.

## Persistencia en base de datos

Los metadatos se guardan en la tabla `image_evidence` de la base biometrica. La implementacion actual conserva los campos operativos pedidos para el flujo de parqueo:

- `image_id`
- `session_id`
- `plate`
- `bucket`
- `object_name`
- `image_type`
- `hash_sha256`
- `encrypted`
- `created_at`
- `expires_at`
- `status`

La tabla conserva ademas otros campos heredados del modelo biometrico para compatibilidad con fases posteriores.

## Relacion con la sesion de parqueo

La sesion mock de parqueo guarda referencias para:

- `entry_face_evidence_id`
- `entry_plate_evidence_id`
- `exit_face_evidence_id`
- `exit_plate_evidence_id`

Ademas se mantiene un `face_mock_id` separado para no romper la validacion simulada ya existente.

## Seguridad

- MinIO se usa por red interna del stack Docker mediante `MINIO_INTERNAL_URL`.
- Se autentica con `MINIO_ROOT_USER` y `MINIO_ROOT_PASSWORD`.
- No se publican buckets.
- No se devuelven URLs de acceso directo.
- La app consume solo el `api-gateway`.
- Se calcula `SHA-256` por cada archivo antes de registrar su referencia.

## Seguridad recomendada

- mantener los buckets privados sin politicas `public`;
- rotar credenciales de MinIO fuera del codigo mediante variables de entorno;
- usar HTTPS o red privada para trafico entre clientes y gateway;
- agregar expiracion y limpieza de objetos temporales en `parking-temp`;
- usar URLs firmadas solo para lectura temporal cuando exista modulo administrativo;
- restringir acceso a metadatos de evidencia segun rol.

## Configuracion relevante

Variables de entorno:

- `MINIO_INTERNAL_URL`
- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`
- `MINIO_BUCKET_FACES`
- `MINIO_BUCKET_PLATES`
- `MINIO_BUCKET_EVIDENCE`
- `MINIO_BUCKET_TEMP`
- `EVIDENCE_DEFAULT_UNIVERSITY_ID`

## Migracion para entornos ya creados

Si el contenedor de PostgreSQL biometrico ya existia antes de esta fase, la tabla `image_evidence` necesita aplicar la migracion:

- [database/postgres-biometrics/migrations/004_extend_image_evidence_for_parking.sql](C:\Users\damia\OneDrive\Documentos\parqueadero\database\postgres-biometrics\migrations\004_extend_image_evidence_for_parking.sql)

Ejemplo desde el host:

```powershell
docker exec -i parking-postgres-biometrics psql -U biometric_user -d parking_biometrics -f /workspace/postgres-biometrics/migrations/004_extend_image_evidence_for_parking.sql
```

Si vas a recrear la base desde cero, el script `database/postgres-biometrics/init/000_apply_biometric_schema.sql` ya incluye esta migracion.

## Prueba recomendada

1. Levantar el stack con Docker Compose.
2. Abrir la app.
3. En entrada, usar:
   - `Seleccionar`
   - `Capturar` si el dispositivo lo soporta
   - o `Usar mock`
4. Pulsar `Subir` para rostro y `Subir` para placa.
5. Verificar que cada bloque muestre el `image_id`.
6. Registrar entrada.
7. Verificar que la autorizacion pase.
8. Abrir MinIO Console en `http://localhost:9001`.
9. Confirmar que existan objetos en:
   - `parking-faces`
   - `parking-plates`
10. Repetir en salida y validar que se agreguen nuevas evidencias.

## Limitaciones actuales

- Las sesiones de parqueo siguen siendo mock y viven en memoria del servicio.
- No existe todavia consulta administrativa de evidencias.
- No existe todavia descarga firmada ni politica de expiracion automatica.
- `university_id` en `image_evidence` usa un identificador tecnico por defecto durante esta fase mock.

## Siguiente fase recomendada

- persistir `parking_sessions` reales en PostgreSQL principal para relacionar evidencias con sesiones durables;
- agregar consulta administrativa por `session_id`, `plate` y rango de fechas;
- incorporar URLs firmadas de lectura temporal para revision autorizada;
- aplicar politicas automaticas de expiracion y limpieza por bucket.
