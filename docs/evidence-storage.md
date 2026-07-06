# Almacenamiento de Evidencias en MinIO

## Objetivo

Este documento describe el flujo de almacenamiento de evidencias para Smart Parking University usando MinIO como repositorio privado de objetos.

La fase actual trabaja en modo mock o mixto:

- la app puede enviar imagenes reales seleccionadas o capturadas;
- tambien puede generar archivos mock para demostracion;
- el backend guarda la evidencia en MinIO y conserva solo referencias en memoria dentro del flujo de parqueo mock.

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
  "created_at": "2026-07-06T12:20:00Z"
}
```

## Flujo de entrada

1. La app prepara dos evidencias:
   - rostro de entrada
   - placa de entrada
2. Cada evidencia se envia a `POST /evidence/upload`.
3. El backend sube el archivo a MinIO y responde con `image_id`.
4. La app llama a `POST /parking/entry` enviando:
   - `face_image_id` para validacion mock
   - `face_evidence_id` con la referencia almacenada
   - `plate_evidence_id` con la referencia almacenada
5. `parking-service` crea la sesion y enlaza esas evidencias con el `session_id`.

## Flujo de salida

1. La app prepara dos evidencias:
   - rostro de salida
   - placa de salida
2. Cada evidencia se envia a `POST /evidence/upload`.
3. La app llama a `POST /parking/exit` con:
   - `face_image_id` para validacion mock
   - `face_evidence_id`
   - `plate_evidence_id`
4. `parking-service` enlaza las referencias a la sesion activa o al registro mock de salida.

## Datos conservados por referencia

Cada evidencia conserva:

- `image_id`
- `bucket`
- `object_name`
- `image_type`
- `session_id`
- `plate`
- `created_at`

En esta fase no se expone una descarga publica ni URL firmada de lectura.

## Relacion con la sesion de parqueo

La sesion mock de parqueo guarda referencias para:

- `entry_face_evidence_id`
- `entry_plate_evidence_id`
- `exit_face_evidence_id`
- `exit_plate_evidence_id`

Ademas se mantiene el `face_image_id` mock original para no romper la validacion simulada ya existente.

## Seguridad

- MinIO se usa por red interna del stack Docker mediante `MINIO_INTERNAL_URL`.
- Se autentica con `MINIO_ROOT_USER` y `MINIO_ROOT_PASSWORD`.
- No se publican buckets.
- No se devuelven URLs de acceso directo.
- La app consume solo el `api-gateway`.

## Configuracion relevante

Variables de entorno:

- `MINIO_INTERNAL_URL`
- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`
- `MINIO_BUCKET_FACES`
- `MINIO_BUCKET_PLATES`
- `MINIO_BUCKET_EVIDENCE`
- `MINIO_BUCKET_TEMP`

## Prueba recomendada

1. Levantar el stack con Docker Compose.
2. Abrir la app.
3. En entrada, usar:
   - `Seleccionar`
   - `Capturar` si el dispositivo lo soporta
   - o `Usar mock`
4. Registrar entrada.
5. Verificar que la autorizacion pase.
6. Abrir MinIO Console en `http://localhost:9001`.
7. Confirmar que existan objetos en:
   - `parking-faces`
   - `parking-plates`
8. Repetir en salida y validar que se agreguen nuevas evidencias.

## Limitaciones actuales

- Las referencias de sesion siguen siendo mock y viven en memoria del servicio.
- No existe todavia consulta administrativa de evidencias.
- No existe todavia descarga firmada ni politica de expiracion automatica.
- No existe todavia persistencia relacional de metadatos de evidencia en PostgreSQL.

## Siguiente fase recomendada

Persistir metadatos de evidencia y relacionarlos de forma durable con `parking_sessions`, `access_events` e `incidents` en PostgreSQL o en la base biometrica segun su nivel de sensibilidad.
