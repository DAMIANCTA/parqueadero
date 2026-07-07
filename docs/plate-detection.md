# Deteccion automatica de placa

## Objetivo

Esta fase reemplaza la digitacion manual de la placa para el operador normal. La app movil captura la evidencia, la sube a MinIO y solicita a `plate-service` una deteccion automatica con pipeline ALPR.

## Flujo operativo

1. El operador presiona `Capturar placa`.
2. La app muestra una guia visual para encuadrar la placa.
3. La app toma la foto o permite seleccionarla.
4. La imagen se sube con `POST /evidence/upload`.
5. La app recibe `image_id`.
6. La app llama `POST /plates/detect`.
7. `plate-service` busca la referencia y descarga la imagen desde MinIO.
8. El servicio evalua calidad, intenta detectar region de placa y luego ejecuta OCR.
9. La app muestra:
   - placa detectada
   - confianza
   - advertencias
   - candidatos
10. Si la confianza es menor a `0.75`, la app bloquea la autorizacion automatica y exige `Reintentar captura`.
11. Solo un operador de seguridad puede corregir la placa manualmente y debe registrar motivo para auditoria.

## Endpoint principal

### `POST /plates/detect`

Request:

```json
{
  "image_id": "d1ecb1d2-6a46-4a6f-9490-f6d831f2f2aa",
  "university_id": "uce",
  "campus_id": "matriz",
  "gate_id": "norte"
}
```

Response cuando detecta:

```json
{
  "status": "DETECTED",
  "plate_text": "AGH430",
  "confidence": 0.91,
  "image_id": "d1ecb1d2-6a46-4a6f-9490-f6d831f2f2aa",
  "bounding_box": {
    "x": 120,
    "y": 80,
    "width": 300,
    "height": 90
  },
  "candidates": [
    {
      "text": "AGH430",
      "confidence": 0.91
    },
    {
      "text": "A6H430",
      "confidence": 0.72
    }
  ],
  "mode": "hybrid",
  "valid_format": true,
  "source": "minio",
  "detector_provider": "yolo",
  "ocr_provider": "easyocr",
  "warnings": []
}
```

Response cuando no detecta:

```json
{
  "status": "NOT_DETECTED",
  "plate_text": null,
  "confidence": 0.0,
  "image_id": "d1ecb1d2-6a46-4a6f-9490-f6d831f2f2aa",
  "bounding_box": null,
  "candidates": [],
  "mode": "hybrid",
  "valid_format": false,
  "source": "minio",
  "detector_provider": "none",
  "ocr_provider": "easyocr",
  "warnings": ["LOW_QUALITY_IMAGE", "PLATE_REGION_NOT_FOUND"]
}
```

## Modos soportados

- `PLATE_DETECTION_MODE=mock`
  - conserva el comportamiento de demostracion;
  - permite pruebas sin OpenCV, OCR ni modelo YOLO;
  - puede devolver resultados simulados.

- `PLATE_DETECTION_MODE=hybrid`
  - es el modo recomendado por defecto;
  - intenta usar YOLO si existe `backend/services/plate-service/models/plate_detector.pt`;
  - si el modelo no existe, devuelve `MODEL_NOT_FOUND` y sigue con OCR sobre la imagen completa o el mejor recorte disponible;
  - no inventa placas si no logra una lectura valida.

- `PLATE_DETECTION_MODE=real`
  - exige modelo YOLO disponible;
  - si no encuentra el modelo, falla claramente con `MODEL_NOT_FOUND`;
  - si la dependencia de YOLO no esta disponible, falla con `YOLO_NOT_AVAILABLE`.

## Pipeline interno

Estructura principal:

- `routes/plates.py`
- `schemas/plates.py`
- `services/minio_client.py`
- `services/image_quality.py`
- `services/plate_detector_yolo.py`
- `services/plate_cropper.py`
- `services/plate_preprocessor.py`
- `services/ocr_reader.py`
- `services/plate_normalizer.py`
- `services/plate_service.py`
- `models/plate_detector.pt`

Pasos del pipeline:

1. Descargar imagen desde MinIO por `image_id`.
2. Evaluar calidad:
   - resolucion
   - nitidez
   - brillo
3. Detectar region de placa con YOLO cuando el modelo existe.
4. Recortar la region detectada.
5. Preprocesar con OpenCV:
   - escala de grises
   - ecualizacion de histograma
   - reduccion de ruido
   - umbral adaptativo
   - Otsu
6. Ejecutar OCR con `EasyOCR` y fallback a `PaddleOCR`.
7. Normalizar texto.
8. Validar patron de placa.
9. Responder con candidatos, confianza y advertencias.

## Normalizacion aplicada

Reglas activas:

- convertir a mayusculas;
- quitar espacios, guiones y caracteres no alfanumericos;
- conservar solo `A-Z` y `0-9`;
- corregir ambiguedades comunes segun posicion:
  - `0 -> O` en el bloque de letras
  - `1 -> I` en el bloque de letras
  - `5 -> S` en el bloque de letras
  - `6 -> G` en el bloque de letras
  - `8 -> B` en el bloque de letras
  - `O -> 0` en el bloque numerico
  - `I -> 1` en el bloque numerico
  - `S -> 5` en el bloque numerico
  - `G -> 6` en el bloque numerico
  - `B -> 8` en el bloque numerico

Formato configurable por entorno:

- `PLATE_PATTERN_REGEX=^[A-Z]{3}\\d{3,4}$`

## Reglas de la app movil

- el usuario normal no escribe la placa;
- el campo de placa detectada es de solo lectura;
- la captura muestra una guia visual para encuadrar la placa;
- si `confidence < 0.75`, la app no permite entrada o salida automatica;
- si no hay lectura valida, se muestra `Reintentar captura`;
- solo seguridad puede corregir manualmente la placa;
- la correccion manual exige motivo.

## Auditoria

Cuando existe correccion manual, la app envia al backend:

- `operator_username`
- `plate_detected_text`
- `plate_detection_confidence`
- `plate_override_reason`

`parking-service` conserva esos datos en auditoria para distinguir:

- placa detectada automaticamente;
- placa corregida por seguridad;
- motivo declarado de la correccion.

## Logs operativos

`plate-service` registra eventos utiles para depuracion:

- `image_id` recibido
- `object_name` descargado
- tamano de imagen
- `quality_score`
- si se encontro `bounding_box`
- texto OCR crudo
- texto normalizado
- confianza final
- advertencias y causa de fallo

## Dependencias del servicio

- `opencv-python-headless`
- `pillow`
- `numpy`
- `easyocr`
- `ultralytics`

`PaddleOCR` queda preparado como fallback opcional del lector OCR.

## Limitaciones actuales

- la precision real depende de la calidad de la foto y de la disponibilidad del modelo YOLO;
- `hybrid` puede operar sin modelo, pero con menor precision al depender solo de OCR;
- la politica de correccion manual en la app sigue siendo una proteccion de interfaz; la validacion fuerte por rol debe reforzarse tambien en backend.
