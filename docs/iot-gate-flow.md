# IoT Gate Flow

Este documento describe la integracion entre `parking-service`, `iot-service`, Mosquitto, la maqueta fisica de la garita y el ESP32.

## Objetivo

La deteccion de placa, reconocimiento facial, pagos y validacion de miembros se mantienen en los microservicios actuales.

La garita fisica solo recibe comandos de apertura o denegacion mediante MQTT:

- `ABRIR`
- `DENEGAR`

Y publica eventos de presencia cuando detecta un vehiculo:

- `PRESENCIA`

## Topicos MQTT

Compatibilidad operativa actual con la maqueta fisica:

- Comando:
  `ucepark/garita/comandos`
- Evento:
  `ucepark/garita/eventos`

Variables relacionadas en `.env`:

```env
MQTT_HOST=mosquitto
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
IOT_ENABLED=true
IOT_GATE_DEFAULT_ID=garita-01
IOT_GATE_COMMAND_TOPIC=ucepark/garita/comandos
IOT_GATE_EVENT_TOPIC=ucepark/garita/eventos
```

## Flujo de entrada

1. La app movil captura placa y rostro.
2. `parking-service` valida la operacion.
3. Si el resultado es `AUTHORIZED`, `parking-service` llama a `iot-service`.
4. `iot-service` publica `ABRIR` en `ucepark/garita/comandos`.
5. El ESP32 abre el servo y actualiza LEDs.
6. Si el ESP32 detecta presencia, publica `PRESENCIA` en `ucepark/garita/eventos`.
7. `iot-service` escucha ese evento y actualiza el estado interno de la garita a `PRESENCE_DETECTED`.

## Flujo de salida

1. La app movil valida placa, rostro y pago o permiso segun el tipo de acceso.
2. Si el resultado es `AUTHORIZED`, `parking-service` llama a `iot-service` para abrir.
3. Si el resultado es `REJECTED`, `parking-service` llama a `iot-service` para denegar.
4. `iot-service` publica:
   - `ABRIR` si la salida es autorizada
   - `DENEGAR` si la salida es rechazada

## Estados manejados por `iot-service`

`GET /gates/{gate_id}/status` devuelve un estado resumido:

- `IDLE`
- `PRESENCE_DETECTED`
- `OPENED`
- `DENIED`
- `OFFLINE`

Tambien devuelve:

- `mqtt_connected`
- `last_event_type`
- `last_event_payload`
- `last_presence_at`
- `last_command`
- `last_command_at`
- `last_reason`

## Endpoints de `iot-service`

### Abrir barrera

`POST /gates/{gate_id}/open`

Body:

```json
{
  "university_id": "uce",
  "campus_id": "matriz",
  "plate": "ABC1234",
  "session_id": "session-001",
  "reason": "entry_granted"
}
```

Publica:

```text
topic: ucepark/garita/comandos
payload: ABRIR
```

### Denegar barrera

`POST /gates/{gate_id}/deny`

Body:

```json
{
  "university_id": "uce",
  "campus_id": "matriz",
  "plate": "ABC1234",
  "session_id": "session-001",
  "reason": "payment_pending"
}
```

Publica:

```text
topic: ucepark/garita/comandos
payload: DENEGAR
```

### Consultar estado

`GET /gates/{gate_id}/status`

Respuesta esperada:

```json
{
  "gate_id": "garita-01",
  "status": "PRESENCE_DETECTED",
  "mqtt_connected": true,
  "command_topic": "ucepark/garita/comandos",
  "event_topic": "ucepark/garita/eventos",
  "last_event_type": "PRESENCE_DETECTED",
  "last_event_payload": "PRESENCIA",
  "last_presence_at": "2026-07-09T20:10:00+00:00",
  "last_command": "ABRIR",
  "last_command_at": "2026-07-09T20:09:58+00:00",
  "last_updated_at": "2026-07-09T20:10:00+00:00",
  "last_reason": "entry_granted"
}
```

## Endpoints expuestos por `api-gateway`

Para portal y clientes web:

- `GET /iot/gates/status/{gate_id}`
- `POST /iot/gates/{gate_id}/open`
- `POST /iot/gates/{gate_id}/deny`

El portal administrativo usa el gateway, no el `iot-service` directo.

## Portal administrativo

La seccion `Garitas / IoT` del portal muestra:

- estado de la garita
- MQTT conectado o desconectado
- ultimo evento de presencia
- ultimo comando enviado
- boton `Abrir manual`
- boton `Denegar / Cerrar`

Ruta:

- [admin-portal](C:\Users\damia\OneDrive\Documentos\parqueadero\web\admin-portal\index.html)

Servido desde:

- `http://localhost:8000/admin-portal`

## Como probar con Mosquitto

### Escuchar eventos de la garita

```powershell
docker exec -it parking-mosquitto sh -lc "mosquitto_sub -h localhost -t 'ucepark/garita/eventos' -v"
```

### Escuchar comandos enviados por el sistema

```powershell
docker exec -it parking-mosquitto sh -lc "mosquitto_sub -h localhost -t 'ucepark/garita/comandos' -v"
```

### Simular presencia desde otra terminal

```powershell
docker exec -it parking-mosquitto sh -lc "mosquitto_pub -h localhost -t 'ucepark/garita/eventos' -m 'PRESENCIA'"
```

### Abrir manualmente desde HTTP

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/iot/gates/garita-01/open `
  -Headers @{ Authorization = "Bearer TU_TOKEN"; "Content-Type" = "application/json" } `
  -Body '{
    "university_id": "uce",
    "campus_id": "matriz",
    "plate": "ABC1234",
    "session_id": "manual-001",
    "reason": "manual_open_admin_portal"
  }'
```

### Consultar estado de la garita

```powershell
Invoke-RestMethod http://localhost:8000/iot/gates/status/garita-01 | ConvertTo-Json -Depth 4
```

## ESP32

El ESP32 esperado por esta fase:

- escucha `ucepark/garita/comandos`
- abre servo con `ABRIR`
- niega o mantiene cerrado con `DENEGAR`
- publica `PRESENCIA` en `ucepark/garita/eventos`
- usa LEDs para indicar estado local

## Alcance de esta fase

- Se integra la maqueta fisica por MQTT.
- No se reemplaza `plate-service`.
- No se reemplaza `face-service`.
- No se mueve la deteccion a `yolo_cpu.py`.
- El control de acceso sigue centralizado en `parking-service`.
