# ESP32

Firmware de la garita fisica (`garita_firmware/`) y utilidades para probar la
deteccion de placa localmente.

El orquestador de garita (deteccion de placa + verificacion facial +
apertura/denegacion de la barrera) ya no vive aca: es un microservicio mas
del backend, en `backend/services/garita-controller/` (corre en Docker
Compose junto a los demas).

Lo que queda en esta carpeta:
- `garita_firmware/`: firmware del ESP32 (sensor de presencia, boton de
  modo, barrera).
- `usb_camera_bridge.py`: puente para poder usar una webcam USB del PC con
  garita-controller en pruebas (Docker Desktop en Windows no puede acceder
  a dispositivos USB del host, asi que este script corre nativo y sirve la
  webcam por HTTP - ver su docstring para el uso completo).
