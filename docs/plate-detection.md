# Deteccion automatica de placa

## Objetivo

Esta fase elimina la digitacion manual de placa para el operador normal. La aplicacion movil captura la imagen de la placa, la sube como evidencia, solicita deteccion automatica y usa el resultado para entrada o salida.

## Flujo operativo

1. El operador presiona `Capturar placa`.
2. La app obtiene la imagen desde camara o galeria.
3. La app sube la imagen mediante `POST /evidence/upload`.
4. La app recibe `plate_image_id`.
5. La app llama `POST /plates/detect`.
6. `plate-service` busca la referencia de `image_id` en la base biometrica.
7. `plate-service` descarga la imagen desde MinIO.
8. `plate-service` ejecuta deteccion mock o preparada.
9. La app muestra:
   - placa detectada
   - confianza
   - candidatos
   - estado de deteccion
10. Si la confianza es suficiente, la placa detectada se usa en:
   - `POST /parking/entry`
   - `POST /parking/exit`

## Endpoint principal

### `POST /plates/detect`

La app consume este endpoint a traves del `api-gateway`.

Request recomendado:

```json
{
  "image_id": "d1ecb1d2-6a46-4a6f-9490-f6d831f2f2aa",
  "university_id": "uce",
  "campus_id": "matriz",
  "gate_id": "norte"
}
```

Response:

```json
{
  "plate_text": "AGH430",
  "confidence": 0.91,
  "image_id": "d1ecb1d2-6a46-4a6f-9490-f6d831f2f2aa",
  "bounding_box": {
    "x": 120,
    "y": 210,
    "width": 260,
    "height": 80
  },
  "candidates": [
    {"text": "AGH430", "confidence": 0.91},
    {"text": "A6H430", "confidence": 0.72}
  ],
  "status": "DETECTED",
  "mode": "mock",
  "valid_format": true,
  "source": "minio",
  "detector_provider": "mock-detector",
  "ocr_provider": "mock-ocr"
}
```

## Modos soportados

- `PLATE_DETECTION_MODE=mock`
  - usa un detector y OCR simulados;
  - permite demos sin modelos pesados;
  - puede derivar una placa desde nombres de archivo, contenido mock o un fallback controlado.

- `PLATE_DETECTION_MODE=real`
  - deja preparado el pipeline para YOLO + OCR;
  - usa placeholders ligeros hasta integrar el runtime real.

## Arquitectura interna

La implementacion actual deja separado el flujo en piezas pequeñas:

- `routes/plates.py`
- `schemas/plates.py`
- `services/plate_detection_service.py`
- `services/plate_detector.py`
- `services/ocr_reader.py`
- `services/minio_client.py`
- `services/plate_normalizer.py`
- `repositories/evidence_reference_repository.py`

Funciones preparadas:

- `download_image_from_minio(image_id)`
- `detect_plate_region(image)`
- `read_plate_text(image)`
- `normalize_plate_text(text)`
- `validate_plate_format(text)`
- `detect_plate(...)`

## Normalizacion aplicada

La fase actual normaliza la placa con estas reglas:

- convierte a mayusculas;
- elimina espacios y guiones;
- corrige caracteres comunes en la parte esperada de letras o numeros;
- valida formato ecuatoriano basico:
  - `3 letras + 3 numeros`
  - `3 letras + 4 numeros`

Ejemplos:

- `agh-430` -> `AGH430`
- `AGO43O` -> `AGO430`
- `a s h 1 2 3 4` -> `ASH1234`

## Reglas de la app movil

- el operador normal no digita la placa;
- el campo de placa se muestra en solo lectura;
- si la deteccion no llega a `0.75`, la app bloquea entrada o salida automatica;
- si falla la deteccion, la app ofrece `Reintentar captura`;
- solo un operador cuyo usuario contenga `security` puede corregir manualmente la placa;
- si hay correccion manual, se exige motivo y se envia al backend para auditoria.

## Auditoria

Cuando la app envia una correccion manual, `parking-service` registra en la metadata de auditoria:

- `operator_username`
- `plate_detected_text`
- `plate_detection_confidence`
- `plate_override_reason`

Esto permite distinguir entre:

- placa detectada automaticamente;
- placa corregida manualmente por seguridad;
- motivo declarado para la correccion.

## Limitaciones actuales

- la deteccion sigue en modo mock avanzado;
- todavia no se ejecuta YOLO ni OCR real;
- la correccion manual depende del nombre de usuario cargado en la app mock, no de RBAC real del backend.

## Siguiente fase recomendada

- integrar YOLO para deteccion de region;
- integrar OCR real;
- almacenar recortes de placa para revision manual;
- agregar revision administrativa de candidatos y bounding box.
