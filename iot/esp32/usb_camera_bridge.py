"""Puente para probar camaras USB del PC con garita-controller (Docker).

Docker Desktop en Windows no puede acceder de forma confiable a dispositivos
USB del host (a diferencia de Linux nativo), asi que garita-controller corre
en Docker usando solo camaras de red (ver PLATE_CAMERA_SOURCE). Para poder
probar igual con una webcam USB sin salir de ese esquema, este script corre
NATIVO en Windows (fuera de Docker, donde SI puede abrir la webcam), lee la
camara y la sirve por HTTP MJPEG - desde el contenedor se ve exactamente
igual que cualquier camara IP.

Uso:
    python usb_camera_bridge.py --camera-index 0 --port 8020

Despues, en el campo "Cambiar camara" de la vista en vivo de garita-controller
(http://localhost:8010/) o en PLATE_CAMERA_SOURCE, usa:
    http://host.docker.internal:8020/stream

"host.docker.internal" es el nombre que Docker Desktop (Windows/Mac) ya
resuelve automaticamente hacia el propio host - no hace falta configurar
nada extra en docker-compose.yml para que el contenedor llegue hasta aca.
"""

import argparse
import threading
import time

import cv2
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera-index", type=int, default=0, help="Indice de la webcam USB (0, 1, ...)")
    parser.add_argument("--port", type=int, default=8020, help="Puerto donde se sirve el stream HTTP")
    args = parser.parse_args()

    cam = cv2.VideoCapture(args.camera_index, cv2.CAP_DSHOW)
    if not cam.isOpened():
        cam = cv2.VideoCapture(args.camera_index)
    if not cam.isOpened():
        raise SystemExit(f"No se pudo abrir la webcam USB indice {args.camera_index}.")
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    latest_jpeg: bytes | None = None
    lock = threading.Lock()
    stop_event = threading.Event()

    def reader_loop() -> None:
        nonlocal latest_jpeg
        while not stop_event.is_set():
            ok, frame = cam.read()
            if ok and frame is not None:
                ok2, buffer = cv2.imencode(".jpg", frame)
                if ok2:
                    with lock:
                        latest_jpeg = buffer.tobytes()
            else:
                time.sleep(0.1)

    threading.Thread(target=reader_loop, daemon=True, name="usb-camera-reader").start()

    def mjpeg_generator():
        boundary = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
        while True:
            with lock:
                frame = latest_jpeg
            if frame is not None:
                yield boundary + frame + b"\r\n"
            time.sleep(0.05)

    app = FastAPI(title="usb-camera-bridge")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/stream")
    def stream() -> StreamingResponse:
        return StreamingResponse(mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return (
            "<html><head><title>Webcam USB - puente</title></head>"
            "<body style='margin:0;background:#111'>"
            "<img src='/stream' style='width:100%;height:100vh;object-fit:contain' />"
            "</body></html>"
        )

    print(f"Sirviendo webcam USB (indice {args.camera_index}) en http://0.0.0.0:{args.port}/")
    print(f"Desde garita-controller (Docker), usa como camara: http://host.docker.internal:{args.port}/stream")
    try:
        uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="warning")
    finally:
        stop_event.set()
        cam.release()


if __name__ == "__main__":
    main()
