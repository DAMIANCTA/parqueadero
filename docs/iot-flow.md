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
2. `iot_service` publica un comando MQTT de apertura.
3. Node-RED consume el mensaje para pruebas, trazabilidad o integracion.
4. En fases posteriores un ESP32 escuchara el topico y accionara la barrera.
5. El dispositivo podra responder con confirmacion de estado.

## Topicos sugeridos

- `smartparking/{university_id}/{campus_id}/{gate_id}/command`
- `smartparking/{university_id}/{campus_id}/{gate_id}/status`
- `smartparking/{university_id}/{campus_id}/{gate_id}/telemetry`

## Rol de Node-RED

- Prototipar integraciones sin firmware final.
- Visualizar eventos rapidamente.
- Transformar payloads.
- Enrutar eventos hacia otros sistemas.

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

## Estado en Fase 1

El repositorio ya deja preparado MQTT, Node-RED y la estructura para ThingsBoard y ESP32, pero la apertura fisica real de la barrera se posterga para fases siguientes.
