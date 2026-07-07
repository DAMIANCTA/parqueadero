# Entrenamiento YOLO para deteccion de placas

## Objetivo

Esta fase prepara un flujo de entrenamiento local para detectar la region de la placa con YOLO sin entrenar dentro del microservicio Docker. El resultado final del entrenamiento debe copiarse al backend como `plate_detector.pt`.

## Estructura creada

```text
training/plate-detector/
  dataset/
    images/
      train/
      val/
      test/
    labels/
      train/
      val/
      test/
    dataset.yaml
  train_yolo.py
  test_model.py
```

## Dataset esperado

El detector usa una sola clase:

- `license_plate`

Archivo de ejemplo:

```yaml
path: training/plate-detector/dataset
train: images/train
val: images/val
test: images/test

names:
  0: license_plate
```

## Formato de etiquetas YOLO

Cada imagen debe tener un archivo `.txt` con el mismo nombre base dentro de `labels/`.

Formato por linea:

```text
class_id x_center y_center width height
```

Todos los valores de coordenadas deben estar normalizados entre `0` y `1`.

Ejemplo:

```text
0 0.512500 0.611111 0.325000 0.118519
```

## Etiquetado de placas

Opciones recomendadas:

### Roboflow

- subir imagenes del dataset;
- crear la clase `license_plate`;
- etiquetar cajas alrededor de cada placa visible;
- exportar en formato `YOLOv8`.

Ventajas:

- rapido para arrancar;
- facilita versionado del dataset;
- permite dividir train/val/test desde la interfaz.

### LabelImg

- abrir carpeta de imagenes;
- crear la etiqueta `license_plate`;
- dibujar bounding boxes;
- guardar en formato YOLO.

Ventajas:

- funciona localmente;
- util para datasets pequenos o medianos;
- simple para trabajo individual.

### CVAT

- crear un proyecto y una tarea;
- registrar la etiqueta `license_plate`;
- etiquetar manualmente o con ayuda semiautomatica;
- exportar en formato YOLO.

Ventajas:

- mejor para trabajo colaborativo;
- muy util cuando hay varios anotadores;
- mas flexible para control de calidad.

## Recomendaciones para el dataset

- usar fotos reales tomadas desde el celular o camaras cercanas al caso de uso;
- incluir placas centradas y tambien casos no perfectos;
- mezclar dia, noche, sombra, lluvia, reflejos y diferentes distancias;
- incluir diferentes angulos de entrada y salida;
- evitar datasets con solo un tipo de encuadre perfecto;
- revisar que no haya imagenes sin etiqueta por error;
- separar train/val/test sin duplicados casi identicos.

Distribucion sugerida:

- `70%` train
- `20%` val
- `10%` test

## Instalacion local recomendada

Este entrenamiento debe ejecutarse fuera del microservicio, en una maquina local con Python.

Paquetes minimos sugeridos:

```bash
pip install ultralytics
```

Si quieres probar predicciones o visualizar mejor resultados, tambien puede ayudarte:

```bash
pip install opencv-python pillow
```

## Script de entrenamiento

Archivo:

- [training/plate-detector/train_yolo.py](C:/Users/damia/OneDrive/Documentos/parqueadero/training/plate-detector/train_yolo.py)

Ejemplo con `yolo11n.pt`:

```bash
python training/plate-detector/train_yolo.py --model yolo11n.pt --epochs 100 --batch 16
```

Ejemplo con `yolo8n.pt`:

```bash
python training/plate-detector/train_yolo.py --model yolo8n.pt --epochs 80 --batch 8
```

Parametros principales:

- `--model`: checkpoint base, por ejemplo `yolo11n.pt` o `yolo8n.pt`
- `--imgsz`: tamano de imagen, por defecto `640`
- `--epochs`: numero de epocas
- `--batch`: batch size
- `--project`: carpeta donde Ultralytics guardara las corridas
- `--name`: nombre de la corrida

## Script de prueba del modelo

Archivo:

- [training/plate-detector/test_model.py](C:/Users/damia/OneDrive/Documentos/parqueadero/training/plate-detector/test_model.py)

Ejemplo:

```bash
python training/plate-detector/test_model.py --model training/plate-detector/runs/detect/train/weights/best.pt --image path/a/tu_imagen.jpg --save
```

El script muestra:

- bounding box
- confidence
- ubicacion de la placa

Salida esperada:

```text
Detection 1: class_id=0 confidence=0.9120 bbox=(x=120.0, y=85.0, width=310.0, height=92.0)
```

Si usas `--save`, Ultralytics guardara una imagen anotada en la carpeta de predicciones.

## Despliegue del modelo entrenado

Cuando el entrenamiento termine, copia:

```text
training/plate-detector/runs/detect/train/weights/best.pt
```

a:

```text
backend/services/plate-service/models/plate_detector.pt
```

En Windows PowerShell:

```powershell
Copy-Item training\plate-detector\runs\detect\train\weights\best.pt backend\services\plate-service\models\plate_detector.pt
```

Despues reconstruye el servicio:

```powershell
docker compose up -d --build plate-service
```

Y verifica:

- [http://127.0.0.1:8006/plates/config](http://127.0.0.1:8006/plates/config)

Debe cambiar:

- `model_exists: true`

## Que no hacer en esta fase

- no subir pesos pesados al repositorio;
- no entrenar dentro del microservicio Docker;
- no cambiar el flujo actual de Flutter;
- no mover todavia el reconocimiento OCR a un pipeline mas complejo sin validar primero la deteccion de la region.

## Siguiente paso recomendado

Una vez que `model_exists` sea `true`, vuelve a probar la app en `hybrid` y revisa si desaparece `MODEL_NOT_FOUND`. A partir de ahi ya podras comparar:

- OCR sobre imagen completa
- OCR sobre recorte de placa detectado por YOLO

y medir si mejora la confianza final.
