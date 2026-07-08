# Face Recognition Flow

## Objetivo

Esta fase mueve `face-service` desde un comportamiento puramente mock a un modo `hybrid` preparado para reconocimiento facial real con dos proveedores posibles:

- `insightface`
- `face_recognition` sobre `dlib`

La integracion mantiene compatibilidad con el flujo actual de entrada, deteccion de placa, pago en Caja y salida.

## Componentes involucrados

- `mobile/app`: captura o seleccion de evidencia facial.
- `api-gateway`: expone `GET /faces/config` y mantiene el consumo centralizado por la app.
- `parking-service`: coordina entrada y salida, y delega deteccion/comparacion facial a `face-service`.
- `face-service`: descarga imagen desde MinIO, detecta rostro, genera embedding y compara similitud.
- `face-service/providers/face_recognition_provider.py`: proveedor alternativo basado en `face_recognition` y `dlib`.
- `postgres-biometrics`: guarda `face_templates` y `biometric_access_logs`.
- `MinIO`: conserva las imagenes faciales en `parking-faces`.

## Proveedores soportados

### InsightFace

- proveedor principal recomendado cuando el runtime y el modelo estan disponibles;
- usa embeddings de 512 dimensiones;
- responde bien en un pipeline moderno de deteccion y comparacion.

### face_recognition / dlib

- proveedor alternativo para reutilizar la logica del prototipo recibido;
- usa:
  - `face_recognition.face_locations`
  - `face_recognition.face_encodings`
  - `face_recognition.face_distance`
  - `face_recognition.compare_faces`
- genera embeddings de 128 dimensiones;
- la comparacion real se interpreta como distancia: `match=true` si `distance <= FACE_SIMILARITY_THRESHOLD`.

## Modos de operacion

- `FACE_SERVICE_MODE=mock`
  - mantiene el comportamiento de prueba anterior.
- `FACE_SERVICE_MODE=hybrid`
  - intenta usar el proveedor definido en `FACE_REAL_PROVIDER`;
  - si OpenCV, InsightFace, `face_recognition`, `dlib` o el runtime seleccionado no estan disponibles, cae temporalmente en proveedor preparado para no romper el flujo;
  - la app oculta el simulador de rostro valido, pero informa si el backend quedo en fallback.
- `FACE_SERVICE_MODE=real`
  - exige runtime real y deja de depender del fallback.

## Configuracion por `.env`

### Opcion A: InsightFace

```env
FACE_SERVICE_MODE=hybrid
FACE_REAL_PROVIDER=insightface
FACE_SIMILARITY_THRESHOLD=0.82
FACE_EMBEDDING_DIMENSIONS=512
FACE_DEFAULT_BUCKET=parking-faces
```

### Opcion B: face_recognition / dlib

```env
FACE_SERVICE_MODE=hybrid
FACE_REAL_PROVIDER=face_recognition
FACE_SIMILARITY_THRESHOLD=0.60
FACE_EMBEDDING_DIMENSIONS=128
FACE_DEFAULT_BUCKET=parking-faces
```

Nota importante:

- el proveedor `face_recognition` trabaja logicamente con 128 dimensiones;
- la persistencia actual en `postgres-biometrics` se adapta para convivir con el esquema existente, sin guardar fotos en PostgreSQL;
- las imagenes siguen quedando en MinIO y los embeddings quedan asociados a la sesion o persona.

## Endpoint de configuracion

`GET /faces/config`

Devuelve el estado del runtime facial:

- `face_service_mode`
- `face_real_provider`
- `similarity_threshold`
- `liveness_threshold`
- `embedding_dimensions`
- `opencv_available`
- `insightface_available`
- `face_recognition_available`
- `provider_available`
- `model_loaded`
- `model_error`
- `active_provider`

La app Flutter usa este endpoint para decidir si debe ocultar el simulador de rostro.

Campos importantes:

- `model_loaded=true`: el runtime real del proveedor activo esta listo.
- `model_loaded=false` y `face_service_mode=hybrid`: el servicio sigue respondiendo, pero con fallback preparado.
- `active_provider`: indica si se esta usando `insightface`, `face_recognition` o un proveedor preparado.
- `provider_available=true`: el proveedor real seleccionado puede ejecutarse.

## Flujo de entrada

1. La app captura o selecciona una imagen facial.
2. La app sube la evidencia a `POST /evidence/upload`.
3. `parking-service` recibe `face_image_id` en `POST /parking/entry`.
4. `parking-service` crea un `session_id` tecnico antes de autorizar.
5. `parking-service` llama a `POST /faces/detect`.
6. `face-service`:
   - consulta `image_evidence` en `postgres-biometrics`;
   - descarga la imagen desde MinIO;
   - detecta el rostro;
   - genera embedding facial;
   - guarda una plantilla en `face_templates` asociando `person_id=session_id`;
   - registra logs tecnicos con `image_id`, `bounding_box`, `embedding_generated`, `quality_score` y `warnings`.
7. Si el rostro fue detectado y el embedding fue generado, la entrada continua.
8. La respuesta de entrada devuelve `face_validation` para que la app muestre el resultado.

## Flujo de salida

1. La app vuelve a capturar o seleccionar una imagen facial.
2. La app la sube a MinIO y envia `face_image_id` en `POST /parking/exit`.
3. `parking-service` busca la sesion activa por placa.
4. Si existe sesion activa, llama a `POST /faces/verify-session`.
5. `face-service`:
   - recupera la plantilla facial guardada en entrada;
   - genera embedding del rostro de salida;
   - compara contra `FACE_SIMILARITY_THRESHOLD` usando la metrica del proveedor activo;
   - registra `similarity`, `match`, `bounding_box` y advertencias.
6. Si el proveedor es `insightface`, la validacion usa similitud coseno.
7. Si el proveedor es `face_recognition`, la validacion usa distancia euclidiana/`face_distance` y se acepta si `distance <= threshold`.
8. Si el rostro coincide, la validacion queda en `MATCH`.
9. Si no coincide, la salida se rechaza con `Face verification failed`.

## Endpoints principales

### `POST /faces/detect`

Request:

```json
{
  "image_id": "uuid",
  "university_id": "uuid",
  "session_id": "uuid"
}
```

Uso:

- detectar rostro de entrada;
- generar embedding;
- guardar plantilla biometrica asociada a la sesion activa.

### `POST /faces/verify-session`

Request:

```json
{
  "university_id": "uuid",
  "session_id": "uuid",
  "probe_image_id": "uuid",
  "similarity_threshold": 0.82
}
```

Uso:

- comparar el rostro de salida con el embedding almacenado en entrada.

Respuesta esperada:

- `detected`
- `match`
- `similarity`
- `threshold`
- `bounding_box`
- `embedding_size`
- `warnings`

### `POST /faces/compare`

Permite comparacion directa entre dos evidencias por `image_id` o por referencias MinIO legacy, reutilizando el proveedor facial activo.

### `POST /faces/liveness`

Permite registrar una verificacion backend de liveness basada en evidencia ya subida. En esta fase sigue siendo una capa preparada; no depende de `InsightFace` ni de `face_recognition`.

## Datos almacenados

### En MinIO

- imagenes faciales originales;
- bucket principal: `parking-faces`;
- no se almacenan fotos dentro de PostgreSQL.

### En `face_templates`

- `university_id`
- `person_id` tecnico
- `source_image_evidence_id`
- `embedding_vector`
- `model_name`
- `quality_score`
- `encrypted`
- `expires_at`
- `status`

El `model_name` deja trazabilidad del proveedor que genero el embedding.

### En `biometric_access_logs`

- tipo de operacion;
- similitud;
- score de calidad;
- score de liveness;
- decision;
- metadata de depuracion y validacion.

## Diferencia entre embeddings 512 vs 128

- `insightface` normalmente trabaja con 512 dimensiones.
- `face_recognition/dlib` trabaja con 128 dimensiones.
- `face-service` expone `embedding_dimensions` segun el proveedor activo en `/faces/config`.
- La comparacion debe hacerse siempre con el mismo proveedor con el que se genero la plantilla de entrada.

## Logs esperados

`face-service` registra como minimo:

- `image_id`
- `detected`
- `bounding_box`
- `embedding_generated`
- `similarity`
- `match`
- `warnings`
- proveedor solicitado y proveedor realmente usado
- `model_loaded` y fallback cuando aplica
- para `face_recognition`: conversion BGR/RGB, bounding box seleccionado y distancia final

`parking-service` incorpora el resumen facial dentro de `face_validation`.

## Comportamiento en Flutter

- cuando `FACE_SERVICE_MODE` es `hybrid` o `real`, la app oculta el switch `Simulador de rostro valido`;
- cuando `FACE_SERVICE_MODE` es `hybrid` o `real`, la app tambien desactiva `Usar mock` para evidencia facial;
- la app conserva el flujo de liveness actual;
- la pantalla de resultado muestra:
  - `Rostro detectado`
  - `MATCH / NO_MATCH`
  - `similarity` o `distance`, segun proveedor
  - `threshold`
  - `model_name`
  - `bounding_box`
  - proveedor y advertencias

## Como probar entrada y salida con rostro real

1. Configurar `.env` con el proveedor deseado.
2. Levantar o reconstruir los servicios:

```powershell
docker compose up -d --build face-service parking-service api-gateway
```

3. Verificar configuracion:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/faces/config | ConvertTo-Json -Depth 4
```

4. En la app Flutter:
   - capturar rostro real en entrada;
   - registrar entrada;
   - capturar rostro real en salida;
   - verificar que la respuesta muestre `MATCH` y el score esperado.
5. Si la salida falla por rostro, `parking-service` debe responder `REJECTED` con `Face verification failed`.

## Consideraciones sobre Docker y dlib

- los `.whl` de Windows que te pasaron no deben usarse dentro del contenedor Linux;
- si deseas activar el proveedor `face_recognition` dentro de Docker, debes usar paquetes compatibles con Linux;
- si `dlib` o `face_recognition` no estan disponibles, `FACE_SERVICE_MODE=hybrid` mantiene el flujo mediante fallback y no rompe el sistema completo.

## Limitaciones actuales

- el modulo de liveness backend sigue siendo una capa preparada, no un motor anti-spoofing productivo;
- para operadores registrados sin una sesion activa previa, el sistema conserva fallback compatible con el flujo anterior;
- InsightFace puede requerir descarga o disponibilidad local de modelos en el contenedor;
- `face_recognition/dlib` puede requerir una instalacion mas pesada en Linux;
- en modo `hybrid`, un fallback preparado evita cortar la demo, pero no reemplaza una verificacion biometrica productiva.
