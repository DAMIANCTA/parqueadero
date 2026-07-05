# Flujo IoT

## Objetivo

Definir como el backend se comunica con el ecosistema IoT encargado de abrir barreras, exponer telemetria y permitir maquetado rapido de integraciones.

## Componentes

- `Mosquitto`: broker MQTT principal.
- `iot_service`: publica eventos y comandos desde backend.
- `Node-RED`: orquesta flujos, transforma mensajes y facilita demos.
- `ThingsBoard`: opcion futura para dashboards, reglas y monitoreo.
- `ESP32`: controlador futuro para barreras, sensores y actuadores.

## Flujo base

1. El backend valida el acceso.
2. `parking-service` invoca `iot-service` cuando la validacion de entrada o salida es autorizada.
3. `iot-service` publica un comando MQTT de apertura.
4. Node-RED consume el mensaje para pruebas, trazabilidad o integracion visual.
5. Node-RED publica de vuelta el estado de la barrera.
6. En fases posteriores un ESP32 escuchara el topico y accionara la barrera real.

## Topicos implementados

- `universities/{university_id}/campuses/{campus_id}/gates/{gate_id}/cmd`
- `universities/{university_id}/campuses/{campus_id}/gates/{gate_id}/status`

## Payload de comando publicado por `iot-service`

```json
{
  "command": "open",
  "plate": "ABC1234",
  "session_id": "0f2b6d0a-7bdf-4cfe-b911-cfef8e0c91a2",
  "reason": "validated"
}
```

## Payload de estado publicado por Node-RED

```json
{
  "barrier": "open",
  "device_status": "online",
  "university_id": "11111111-1111-1111-1111-111111111111",
  "campus_id": "22222222-2222-2222-2222-222222222222",
  "gate_id": "33333333-3333-3333-3333-333333333331",
  "plate": "ABC1234",
  "reason": "validated",
  "last_event": "open requested at 2026-07-05T12:00:00.000Z",
  "updated_at": "2026-07-05T12:00:01.000Z"
}
```

## Rol de Node-RED

- Prototipar integraciones sin firmware final.
- Visualizar eventos rapidamente.
- Transformar payloads.
- Enrutar eventos hacia otros sistemas.
- Publicar una vista HTTP simple para exposicion o pruebas.

## Vista de Node-RED

La maqueta actual expone `http://localhost:1880/parking-dashboard` y muestra:

- Universidad
- Campus
- Puerta
- Placa
- Estado de barrera
- Motivo de apertura
- Ultimo evento

## Como probar la integracion simulada

1. Copia `.env.example` a `.env` si todavia no existe.
2. Levanta el entorno:

```powershell
docker compose up --build
```

3. Verifica servicios base:

- API de parqueo: `http://localhost:8004/health`
- IoT service: `http://localhost:8008/health`
- Node-RED: `http://localhost:1880`
- Dashboard Node-RED: `http://localhost:1880/parking-dashboard`

4. Publica un comando manual hacia `iot-service`:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8008/api/v1/gates/open `
  -ContentType 'application/json' `
  -Body '{
    "university_id": "11111111-1111-1111-1111-111111111111",
    "campus_id": "22222222-2222-2222-2222-222222222222",
    "gate_id": "33333333-3333-3333-3333-333333333331",
    "plate": "ABC1234",
    "session_id": "demo-session-001",
    "reason": "validated"
  }'
```

5. Abre `http://localhost:1880/parking-dashboard` y confirma que aparezcan universidad, campus, puerta, placa, estado de barrera y motivo.
6. En el editor de Node-RED, revisa la barra lateral `debug` para ver el comando recibido y el estado publicado.
7. Para probar el flujo completo, ejecuta una entrada o salida autorizada desde `parking-service`; cuando el acceso sea valido, este servicio llamara a `iot-service` y se generara el mismo evento MQTT.

## Rol futuro de ThingsBoard

- Dashboards de estado por campus y puerta.
- Alarmas y reglas operativas.
- Telemetria historica de dispositivos.
- Monitoreo de disponibilidad de barreras y controladores.

## Rol futuro de ESP32

- Recibir comando de apertura o cierre.
- Activar servomotor o rele.
- Reportar sensores de barrera.
- Reportar heartbeat del dispositivo.

## Estado en Fase 10

La fase actual deja Mosquitto, `iot-service` y Node-RED integrados en modo simulado. La barrera fisica real sigue diferida para una fase posterior con ESP32.
