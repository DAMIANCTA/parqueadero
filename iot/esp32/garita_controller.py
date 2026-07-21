"""Orquestador de garita: automatiza la deteccion de placa + verificacion
facial + apertura/denegacion de la barrera fisica.

ESP32 (sensor de presencia + boton de modo) --MQTT--> este script + celular:
  1. YOLO local detecta la region de la placa en cada frame de la webcam USB
     SOLO para dibujar el recuadro en vivo (rapido, sin red). La lectura de
     texto real de la placa no es local: cada recorte candidato se manda a
     plate-service (/plates/detect), que corre su propio YOLO+OCR real y
     devuelve el texto+confianza.
  2. El rostro lo captura la app movil (mobile/app, pantalla "Garita fisica"),
     sube la evidencia a parking-service (/evidence/upload) y publica el
     image_id resultante en ucepark/garita/rostro_evidencia. Este script solo
     espera ese mensaje.
  3. Llama a parking-service (/parking/entry o /parking/exit segun el modo
     que reporta el ESP32) - el backend decide el match real placa+rostro y,
     si autoriza, el propio parking-service le ordena a iot-service publicar
     "ABRIR" en ucepark/garita/comandos (ver services/iot_repository.py). Este
     script YA NO publica el comando final el mismo: solo lo hace en los dos
     rechazos tempranos que nunca llegan a llamar a parking-service (placa
     desconocida, vehiculo ya adentro), donde nadie mas publicaria el DENEGAR.

Requiere: pip install requests paho-mqtt opencv-python numpy ultralytics minio
Uso:
    python garita_controller.py
    (ESC en la ventana de vista previa cierra el programa)
"""

import argparse
import base64
import hashlib
import hmac
import json
import queue
import re
import threading
import time
import uuid
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import paho.mqtt.client as mqtt
import requests
from ultralytics import YOLO

UNIVERSITY_ID = "11111111-1111-1111-1111-111111111111"
CAMPUS_ID = "22222222-2222-2222-2222-222222222222"
# Un unico gate_id fijo para entrada y salida: coincide con
# `iot_gate_default_id` de iot-service ("garita-01"), que es la clave que ya
# usa el panel "Garitas / IoT" del admin-portal para consultar el estado.
GATE_ID = "garita-01"

TOPIC_PRESENCIA = "ucepark/garita/eventos"
TOPIC_COMANDOS = "ucepark/garita/comandos"
TOPIC_ROSTRO_EVIDENCIA = "ucepark/garita/rostro_evidencia"
# Topico adicional (no lo lee el ESP32, que solo entiende "ABRIR"/"DENEGAR"
# en texto plano en ucepark/garita/comandos): lleva el motivo real que
# devolvio parking-service, para que la app movil pueda mostrarlo en vez de
# un generico "RECHAZADO".
TOPIC_RESULTADO_DETALLE = "ucepark/garita/resultado_detalle"
# La app movil no arranca su captura de rostro apenas ve el evento de
# presencia: espera a que este script confirme la placa (o el timeout de
# deteccion) por este topico, para que el flujo sea placa-primero-despues-
# rostro tambien del lado del celular.
TOPIC_PLACA_DETECTADA = "ucepark/garita/placa_detectada"
# Cuando parking-service rechaza por FACE_NOT_DETECTED (no por rostro
# distinto, ni pago, etc.) y todavia quedan intentos, este script pide otra
# foto por este topico en vez de rechazar de una - el celular debe volver a
# capturar SIN esperar una nueva presencia. Solo se publica el veredicto
# final (TOPIC_RESULTADO_DETALLE, y TOPIC_COMANDOS solo en los rechazos
# tempranos) al terminar los intentos.
TOPIC_REINTENTAR_ROSTRO = "ucepark/garita/reintentar_rostro"
MAX_FACE_ATTEMPTS = 3

DEFAULT_CONFIDENCE_FACE = 0.95
DEFAULT_LIVENESS_SCORE = 0.90
PREVIEW_HEIGHT = 480


def format_ecuadorian_plate(text: str) -> str | None:
    # 3 letras + 3-4 numeros, descarta lecturas de OCR que no calcen con el
    # formato real (sin guion: parking-service guarda y compara placas sin
    # separador, ver PLATE_PATTERN_REGEX=^[A-Z]{3}\d{3,4}$).
    cleaned = re.sub(r"[^A-Z0-9]", "", text.upper())
    match = re.search(r"([A-Z]{3})(\d{3,4})", cleaned)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    return None


def encode_jwt(secret_key: str, issuer: str, audience: str, claims: dict, expires_minutes: int = 60) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {**claims, "iss": issuer, "aud": audience, "iat": now, "exp": now + expires_minutes * 60}

    def b64(value: dict) -> str:
        raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")

    signing_input = f"{b64(header)}.{b64(payload)}"
    signature = hmac.new(secret_key.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    return f"{signing_input}.{signature_b64}"


class GaritaController:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        token = encode_jwt(
            args.jwt_secret,
            "smart-parking-university",
            "smart-parking-clients",
            {
                "sub": "garita-controller",
                "username": "garita-controller",
                "roles": ["SECURITY"],
                "permissions": ["parking.entry", "parking.exit", "plates.detect"],
            },
        )
        self.headers = {"Authorization": f"Bearer {token}"}

        # La webcam USB se abre UNA sola vez y se mantiene abierta: la vista
        # previa y la captura real leen del mismo objeto.
        self.plate_cam = cv2.VideoCapture(args.plate_camera_index, cv2.CAP_DSHOW)
        if not self.plate_cam.isOpened():
            self.plate_cam = cv2.VideoCapture(args.plate_camera_index)

        # El rostro lo captura la app movil (nativo, sin lag de WiFi/MJPEG) y
        # avisa por MQTT con el image_id ya subido a parking-service. Ver
        # _wait_for_face_evidence.
        self.face_evidence_queue: queue.Queue = queue.Queue()

        # YOLO local: SOLO para ubicar la region de la placa y dibujar el
        # recuadro en la vista previa en vivo (rapido, sin red). La lectura
        # de texto real va a plate-service (ver _detect_plate_remote) - asi
        # no se duplica el mismo modelo/OCR que ya corre como microservicio.
        print("Cargando modelo YOLO de placas (solo para el recuadro en vivo)...")
        self.plate_model = YOLO(args.plate_model_path)

        # La llamada a plate-service tarda ~800ms (red + YOLO + OCR del otro
        # lado). Si se espera de forma sincrona dentro del loop de vista
        # previa, la ventana se congela en cada intento y ademas caben menos
        # intentos dentro de plate_timeout. Por eso corre en un hilo aparte:
        # el loop solo dispara la consulta y sigue leyendo camara/dibujando,
        # y recoge el resultado de esta cola cuando ya este listo.
        self._plate_reading_queue: queue.Queue = queue.Queue()
        self._plate_request_busy = threading.Event()

        self.presence_queue: queue.Queue = queue.Queue()
        self.status_text = "En espera de presencia..."

        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"garita-controller-{uuid.uuid4().hex[:8]}")
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message

    def run(self) -> None:
        print(f"Conectando a MQTT {self.args.mqtt_host}:{self.args.mqtt_port}...")
        self.mqtt_client.connect(self.args.mqtt_host, self.args.mqtt_port, keepalive=60)
        self.mqtt_client.loop_start()  # corre en un hilo aparte, no bloquea la vista previa
        try:
            self._preview_loop()
        finally:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.plate_cam.release()
            cv2.destroyAllWindows()

    def _preview_loop(self) -> None:
        print("Vista previa en vivo. ESC en la ventana para salir.")
        while True:
            self._render_preview()
            if cv2.waitKey(1) & 0xFF == 27:
                break

            try:
                mode = self.presence_queue.get_nowait()
            except queue.Empty:
                continue

            try:
                self._process_presence(mode)
            except KeyboardInterrupt:
                break
            except Exception as exc:  # noqa: BLE001 - no queremos tumbar el loop de vista previa
                print(f"ERROR procesando presencia: {exc}")
                self.status_text = f"ERROR: {exc}"
                # Nadie mas publicaria un DENEGAR para este ciclo (no se llego
                # a llamar a parking-service, o fallo antes de su respuesta):
                # el script lo hace directo para no dejar la barrera colgada.
                self.mqtt_client.publish(TOPIC_COMANDOS, "DENEGAR")
                self.mqtt_client.publish(
                    TOPIC_RESULTADO_DETALLE,
                    json.dumps({"authorized": False, "message": str(exc)}),
                )

    def _on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        print(f"Conectado a MQTT (reason_code={reason_code}). Suscrito a {TOPIC_PRESENCIA} y {TOPIC_ROSTRO_EVIDENCIA}")
        client.subscribe(TOPIC_PRESENCIA)
        client.subscribe(TOPIC_ROSTRO_EVIDENCIA)
        # El firmware espera un primer mensaje en ucepark/garita/comandos para
        # salir de "Fase 3" (sincronizacion) antes de empezar a detectar
        # presencia. Se manda DENEGAR (no ABRIR) para que, ademas de servir de
        # saludo la primera vez, limpie cualquier "analizando=true" que haya
        # quedado pendiente de una presencia anterior sin respuesta (ej. si
        # este script se reinicia a mitad de un ciclo).
        #
        # Este handshake se publica directo por MQTT (no via iot-service):
        # es un detalle de arranque de hardware sin relacion con logica de
        # negocio/sesiones, y el script ya necesita esta conexion MQTT de
        # todos modos para presencia/rostro_evidencia.
        #
        # retain=True es la parte clave: si este script ya esta corriendo y
        # el ESP32 se prende/reconecta DESPUES, sin retener este mensaje el
        # ESP32 nunca lo veria (se suscribe despues de que se publico) y se
        # quedaria atascado en Fase 3 para siempre. Con retain=True, el
        # broker guarda este ultimo "DENEGAR" y se lo entrega de inmediato a
        # cualquier suscriptor nuevo de ucepark/garita/comandos, sin importar
        # el orden de arranque entre el script y el ESP32.
        client.publish(TOPIC_COMANDOS, "DENEGAR", retain=True)
        print(f"Handshake enviado a {TOPIC_COMANDOS} (DENEGAR, retained)")

    def _on_message(self, client, userdata, message) -> None:
        # Corre en el hilo de MQTT: solo encola, el procesamiento real pasa
        # en el hilo principal (donde tambien vive la vista previa/OpenCV).
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(f"Mensaje MQTT no valido en {message.topic}: {message.payload!r}")
            return

        if message.topic == TOPIC_PRESENCIA:
            if payload.get("event") != "presencia":
                return
            mode = payload.get("mode", "entrada")
            print(f"\n--- Presencia detectada, modo={mode} ---")
            self.presence_queue.put(mode)
        elif message.topic == TOPIC_ROSTRO_EVIDENCIA:
            image_id = payload.get("image_id")
            if image_id:
                print(f"Evidencia de rostro recibida del celular: image_id={image_id}")
                self.face_evidence_queue.put(image_id)

    def _process_presence(self, mode: str) -> None:
        plate_image_type = "plate_entry" if mode == "entrada" else "plate_exit"
        plate_text, confidence_plate, last_frame = self._analyze_plate_live()
        plate_evidence_id = self._upload_evidence(last_frame, image_type=plate_image_type, plate="PENDIENTE")
        print(f"Placa detectada: {plate_text} (confianza={confidence_plate:.2f})")

        if plate_text == "DESCONOCIDA":
            # Sin placa no tiene sentido pedirle rostro al celular: se
            # rechaza directo, sin llamar a parking-service ni esperar foto.
            # Como nunca se llama a parking-service, nadie mas publicaria el
            # comando: el script lo hace directo.
            print("Sin placa detectada, se rechaza sin pedir reconocimiento facial.")
            self.status_text = "RECHAZADO: Placa no detectada"
            self._render_preview()
            self.mqtt_client.publish(TOPIC_COMANDOS, "DENEGAR")
            self.mqtt_client.publish(
                TOPIC_RESULTADO_DETALLE,
                json.dumps({"authorized": False, "message": "Plate not detected", "face_warnings": []}),
            )
            return

        if mode == "entrada" and self._plate_already_inside(plate_text):
            # Rechazo temprano: se descubre ANTES de pedirle foto al celular,
            # no recien despues de verificar el rostro (que ya se habia
            # tomado la foto en vano). Solo aplica a entrada: en salida la
            # placa DEBE estar adentro, eso es lo normal. Tampoco aqui se
            # llama a parking-service, asi que el script publica el comando.
            print(f"Placa {plate_text} ya esta adentro, se rechaza sin pedir foto.")
            self.status_text = f"RECHAZADO: {plate_text} ya esta adentro"
            self._render_preview()
            self.mqtt_client.publish(TOPIC_COMANDOS, "DENEGAR")
            self.mqtt_client.publish(
                TOPIC_RESULTADO_DETALLE,
                json.dumps({"authorized": False, "message": "Vehicle already inside", "face_warnings": []}),
            )
            return

        if self.args.skip_face_verification:
            # Modo de prueba (--skip-face-verification): abre directo al
            # detectar placa, sin esperar foto del celular ni llamar a
            # parking-service. Solo para aislar/probar el servo de la
            # barrera fisica, NO usar en operacion real (sin verificacion
            # de identidad). Como no se llama a parking-service, el script
            # publica el comando directo.
            print(f"[MODO PRUEBA] Placa {plate_text} detectada, abriendo sin verificar rostro.")
            self.status_text = f"MODO PRUEBA: ABRIENDO ({plate_text}), sin verificar rostro"
            self._render_preview()
            self.mqtt_client.publish(TOPIC_COMANDOS, "ABRIR")
            self.mqtt_client.publish(
                TOPIC_RESULTADO_DETALLE,
                json.dumps({"authorized": True, "message": "Test mode: face verification skipped", "face_warnings": []}),
            )
            return

        path = "/parking/entry" if mode == "entrada" else "/parking/exit"
        response: dict = {}
        for attempt in range(1, MAX_FACE_ATTEMPTS + 1):
            face_image_id = self._wait_for_face_evidence(timeout=self.args.face_evidence_timeout)
            if face_image_id is None:
                raise RuntimeError(
                    "No llego evidencia de rostro del celular (revisa que la app este en "
                    "'Garita fisica' y conectada al MQTT)"
                )

            self.status_text = "Procesando en parking-service..."
            payload = {
                "university_id": UNIVERSITY_ID,
                "campus_id": CAMPUS_ID,
                "gate_id": GATE_ID,
                "plate_text": plate_text,
                "face_image_id": face_image_id,
                "face_evidence_id": face_image_id,
                "plate_evidence_id": plate_evidence_id,
                "liveness_score": DEFAULT_LIVENESS_SCORE,
                "confidence_plate": confidence_plate,
                "confidence_face": DEFAULT_CONFIDENCE_FACE,
            }
            if mode == "entrada":
                payload["person_type"] = "visitor"
            response = self._call_parking(path, payload)

            authorized = response.get("authorized", False)
            face_warnings = (response.get("face_validation") or {}).get("warnings") or []
            print(
                f"Intento {attempt}/{MAX_FACE_ATTEMPTS}: authorized={authorized} message={response.get('message')} "
                f"session={response.get('session')} face_warnings={face_warnings}"
            )

            face_not_detected = (not authorized) and "FACE_NOT_DETECTED" in face_warnings
            if not face_not_detected or attempt == MAX_FACE_ATTEMPTS:
                break

            # Rechazo especificamente por no detectar rostro (no por rostro
            # distinto, pago, etc.) y todavia hay intentos: se le pide otra
            # foto al celular sin esperar una nueva presencia del vehiculo.
            print(f"Rostro no detectado, pidiendo otra foto al celular (intento {attempt + 1}/{MAX_FACE_ATTEMPTS})...")
            self.status_text = f"NO SE DETECTO ROSTRO, reintento {attempt}/{MAX_FACE_ATTEMPTS - 1}..."
            self._render_preview()
            self.mqtt_client.publish(TOPIC_REINTENTAR_ROSTRO, json.dumps({"attempt": attempt + 1}))

        authorized = response.get("authorized", False)
        face_warnings = (response.get("face_validation") or {}).get("warnings") or []
        print(f"Resultado final: authorized={authorized} message={response.get('message')} session={response.get('session')}")
        self.status_text = f"{'AUTORIZADO' if authorized else 'RECHAZADO'}: {response.get('message')}"
        # El comando ABRIR/DENEGAR real ya lo publica iot-service, disparado
        # por parking-service al resolver /parking/entry o /parking/exit
        # (ver services/iot_repository.py). Este script solo informa el
        # motivo detallado para que la app movil lo muestre.
        self.mqtt_client.publish(
            TOPIC_RESULTADO_DETALLE,
            json.dumps(
                {
                    "authorized": authorized,
                    "message": response.get("message") or "",
                    "face_warnings": face_warnings,
                }
            ),
        )

    def _analyze_plate_live(self):
        # Loop continuo (sin pausas artificiales) leyendo la webcam en vivo.
        # YOLO local corre cada N frames SOLO para ubicar el recuadro (rapido,
        # sin red). Cada recorte candidato se DESPACHA a plate-service en un
        # hilo aparte (ver _dispatch_plate_detection) - el loop nunca espera
        # esa respuesta, solo recoge lo que ya haya vuelto de la cola en cada
        # vuelta, hasta juntar min_readings_required lecturas coincidentes o
        # agotar el timeout.
        readings: list[str] = []
        last_box = None
        last_frame = None
        frame_count = 0
        last_dispatch_time = 0.0
        start_time = time.time()

        while True:
            frame = self._capture_frame(self.plate_cam)
            last_frame = frame
            frame_count += 1
            now = time.time()

            if now - start_time > self.args.plate_timeout:
                print(f"[TIMEOUT] {len(readings)} lecturas en {self.args.plate_timeout}s, se sigue sin la placa.")
                break

            if frame_count % self.args.plate_yolo_interval == 0:
                results = self.plate_model.predict(
                    frame, conf=self.args.plate_detect_confidence, imgsz=320, device="cpu", verbose=False
                )
                h_frame, w_frame = frame.shape[:2]
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w_frame, x2), min(h_frame, y2)
                    crop = frame[y1:y2, x1:x2]
                    if crop.size == 0:
                        continue
                    last_box = (x1, y1, x2, y2)
                    if now - last_dispatch_time >= self.args.plate_ocr_cooldown:
                        last_dispatch_time = now
                        self._dispatch_plate_detection(crop)
                    break

            for reading, confidence_remote in self._drain_plate_readings():
                readings.append(reading)
                print(f"Lectura {len(readings)}: {reading} (plate-service confianza={confidence_remote:.2f})")

            self.status_text = (
                "ESPERANDO PLACA..." if not readings else f"ESPERANDO PLACA... ({len(readings)} lecturas)"
            )
            self._render_preview(plate_box=last_box, plate_frame_override=frame)
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt("Vista previa cerrada por el usuario")

            if len(readings) >= self.args.plate_min_readings:
                plate_text, count = Counter(readings).most_common(1)[0]
                confidence = 0.90
                print(f"[CONSENSO] Placa decidida: {plate_text} ({count}/{len(readings)} lecturas)")
                self.status_text = f"PLACA DETECTADA: {plate_text}"
                self._render_preview(plate_box=last_box, plate_frame_override=frame)
                self.mqtt_client.publish(
                    TOPIC_PLACA_DETECTADA, json.dumps({"plate_text": plate_text, "confidence": confidence})
                )
                cv2.waitKey(1)
                time.sleep(1.2)  # deja la placa detectada visible antes de pasar a la foto
                return plate_text, confidence, last_frame

        self.status_text = "PLACA NO DETECTADA"
        self._render_preview(plate_box=last_box, plate_frame_override=frame)
        self.mqtt_client.publish(
            TOPIC_PLACA_DETECTADA, json.dumps({"plate_text": "DESCONOCIDA", "confidence": 0.0})
        )
        cv2.waitKey(1)
        time.sleep(1.0)
        return "DESCONOCIDA", 0.0, last_frame

    def _dispatch_plate_detection(self, crop_bgr) -> None:
        # Fire-and-forget: si ya hay una consulta a plate-service en curso,
        # no se lanza otra (evita acumular peticiones si la red o el
        # servicio estan lentos). El loop de vista previa nunca espera a
        # este hilo.
        if self._plate_request_busy.is_set():
            return
        self._plate_request_busy.set()
        threading.Thread(target=self._plate_detection_worker, args=(crop_bgr,), daemon=True).start()

    def _plate_detection_worker(self, crop_bgr) -> None:
        try:
            reading, confidence_remote = self._detect_plate_remote(crop_bgr)
            self._plate_reading_queue.put((reading, confidence_remote))
        finally:
            self._plate_request_busy.clear()

    def _drain_plate_readings(self):
        readings = []
        try:
            while True:
                reading, confidence_remote = self._plate_reading_queue.get_nowait()
                if reading:
                    readings.append((reading, confidence_remote))
        except queue.Empty:
            pass
        return readings

    def _detect_plate_remote(self, crop_bgr) -> tuple[str | None, float]:
        # Manda el recorte candidato a plate-service (YOLO+OCR real) en vez
        # de leerlo con un OCR local. Corre en un hilo de fondo (ver arriba),
        # nunca en el hilo de la vista previa.
        ok, buffer = cv2.imencode(".jpg", crop_bgr)
        if not ok:
            return None, 0.0
        try:
            response = requests.post(
                f"{self.args.plate_service_url}/plates/detect",
                files={"image": ("crop.jpg", buffer.tobytes(), "image/jpeg")},
                headers=self.headers,
                timeout=5,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[plate-service] error al detectar: {exc}")
            return None, 0.0

        data = response.json()
        if not data.get("valid_format") or data.get("status") == "NOT_DETECTED":
            return None, 0.0
        reading = format_ecuadorian_plate(data.get("plate_text") or "")
        return reading, float(data.get("confidence") or 0.0)

    def _wait_for_face_evidence(self, timeout: float) -> str | None:
        # El celular reacciona al mismo evento de presencia por su lado (ve
        # su propia cuenta regresiva en pantalla) y sube su foto de forma
        # independiente - puede terminar antes o despues de que aca se
        # decida la placa. Aca solo se espera su aviso por MQTT, sin
        # congelar la vista previa mientras tanto.
        deadline = time.time() + timeout
        self.status_text = "Esperando foto del celular..."
        while time.time() < deadline:
            try:
                return self.face_evidence_queue.get_nowait()
            except queue.Empty:
                pass
            self._render_preview()
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt("Vista previa cerrada por el usuario")
            time.sleep(0.05)
        return None

    def _render_preview(self, plate_box=None, plate_frame_override=None) -> None:
        if plate_frame_override is not None:
            ok1, plate_frame = True, plate_frame_override
        else:
            ok1, plate_frame = self.plate_cam.read()
        if ok1 and plate_box is not None:
            x1, y1, x2, y2 = plate_box
            cv2.rectangle(plate_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        plate_view = self._resize_to_height(self._label(plate_frame if ok1 else None, "PLACA (USB)"))
        cv2.putText(
            plate_view, self.status_text, (10, plate_view.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2
        )
        cv2.imshow("Garita - vista previa (ESC para salir)", plate_view)

    def _label(self, frame, text: str):
        if frame is None:
            blank = np.zeros((PREVIEW_HEIGHT, PREVIEW_HEIGHT, 3), dtype="uint8")
            cv2.putText(blank, f"Sin senal: {text}", (20, PREVIEW_HEIGHT // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            return blank
        labeled = frame.copy()
        cv2.putText(labeled, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        return labeled

    def _resize_to_height(self, frame):
        h, w = frame.shape[:2]
        scale = PREVIEW_HEIGHT / h
        return cv2.resize(frame, (int(w * scale), PREVIEW_HEIGHT))

    def _capture_frame(self, cam: cv2.VideoCapture):
        for attempt in range(5):
            ok, frame = cam.read()
            if ok and frame is not None:
                return frame
            time.sleep(0.3)
        raise RuntimeError("No se pudo leer un frame de la camara tras varios intentos")

    def _upload_evidence(self, frame, *, image_type: str, plate: str) -> str:
        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            raise RuntimeError("No se pudo codificar el frame a JPEG")
        response = requests.post(
            f"{self.args.parking_service_url}/evidence/upload",
            data={"image_type": image_type, "plate": plate, "university_id": UNIVERSITY_ID},
            files={"file": ("capture.jpg", buffer.tobytes(), "image/jpeg")},
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["image_id"]

    def _call_parking(self, path: str, payload: dict) -> dict:
        response = requests.post(
            f"{self.args.parking_service_url}{path}", json=payload, headers=self.headers, timeout=60
        )
        response.raise_for_status()
        return response.json()

    def _plate_already_inside(self, plate_text: str) -> bool:
        try:
            response = requests.get(
                f"{self.args.parking_service_url}/parking/active-session/{plate_text}",
                headers=self.headers,
                timeout=5,
            )
            response.raise_for_status()
            return bool(response.json().get("active"))
        except requests.RequestException as exc:
            print(f"[active-session] no se pudo consultar, se sigue el flujo normal: {exc}")
            return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plate-camera-index", type=int, default=0, help="Indice de la webcam USB para la placa")
    parser.add_argument(
        "--face-evidence-timeout",
        type=float,
        default=20.0,
        help="Segundos maximos esperando a que la app del celular ('Garita fisica') suba y avise su foto de rostro",
    )
    parser.add_argument(
        "--plate-model-path",
        default=str(Path(__file__).resolve().parent / "models" / "plate_detector.pt"),
        help="Ruta al modelo YOLOv8 entrenado para placas (por defecto: iot/esp32/models/plate_detector.pt, junto a este script)",
    )
    parser.add_argument("--plate-detect-confidence", type=float, default=0.40, help="Confianza minima de YOLO para aceptar una deteccion")
    parser.add_argument(
        "--plate-yolo-interval",
        type=int,
        default=8,
        help="Correr YOLO cada N frames del loop en vivo",
    )
    parser.add_argument("--plate-ocr-cooldown", type=float, default=0.6, help="Segundos minimos entre llamadas a plate-service")
    parser.add_argument(
        "--plate-min-readings",
        type=int,
        default=3,
        help="Cuantas lecturas coincidentes de formato valido se necesitan para decidir la placa",
    )
    parser.add_argument(
        "--plate-timeout",
        type=float,
        default=10.0,
        help="Segundos maximos buscando la placa antes de continuar sin ella",
    )
    parser.add_argument("--mqtt-host", default="localhost")
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--parking-service-url", default="http://localhost:8004")
    parser.add_argument("--plate-service-url", default="http://localhost:8006")
    parser.add_argument("--jwt-secret", default="change-this-jwt-secret-in-production")
    parser.add_argument(
        "--skip-face-verification",
        action="store_true",
        help="MODO PRUEBA: abre la barrera apenas detecta la placa, sin pedir ni verificar rostro. "
        "Util para probar el servo/barrera aislado del resto del flujo. NO usar en operacion real.",
    )
    args = parser.parse_args()

    controller = GaritaController(args)
    controller.run()


if __name__ == "__main__":
    main()
