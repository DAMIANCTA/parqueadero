# Verificacion e Integracion Local

## Objetivo

Este documento describe como validar la integracion local entre la app Flutter, `api-gateway`, microservicios backend, PostgreSQL, MinIO, MQTT y Node-RED sin depender todavia de modelos reales de IA.

## 1. Servicios y puertos

La composicion local definida en [docker-compose.yml](C:\Users\damia\OneDrive\Documentos\parqueadero\docker-compose.yml) expone los siguientes servicios:

| Servicio | Contenedor | Puerto host | Uso |
|---|---|---:|---|
| PostgreSQL core | `parking-postgres-core` | `5432` | Datos transaccionales principales |
| PostgreSQL biometrico | `parking-postgres-biometrics` | `5433` | Plantillas y evidencia biometrica |
| MinIO API | `parking-minio` | `9000` | API S3 compatible |
| MinIO Console | `parking-minio` | `9001` | Consola web de objetos |
| MQTT broker | `parking-mosquitto` | `1883` | Mensajeria IoT |
| MQTT over WebSocket | `parking-mosquitto` | `9002` | Acceso MQTT por WebSocket |
| Node-RED | `parking-nodered` | `1880` | Maqueta visual e integracion |
| API Gateway | `parking-api-gateway` | `8000` | Punto unico de entrada para la app |
| Auth service | `parking-auth-service` | `8001` | Autenticacion JWT |
| University service | `parking-university-service` | `8002` | Universidades, campus y puertas |
| Vehicle service | `parking-vehicle-service` | `8003` | Vehiculos y autorizaciones |
| Parking service | `parking-service` | `8004` | Entradas y salidas |
| Face service | `parking-face-service` | `8005` | Biometria mock/preparada |
| Plate service | `parking-plate-service` | `8006` | OCR/mock de placas |
| Payment service | `parking-payment-service` | `8007` | Cobros y pagos |
| IoT service | `parking-iot-service` | `8008` | Publicacion MQTT |
| Audit service | `parking-audit-service` | `8009` | Bitacora y auditoria |

## 2. Punto de entrada recomendado

La app Flutter debe consumir siempre el `api-gateway`:

- Local Windows: `http://localhost:8000`
- Emulador Android: `http://10.0.2.2:8000`
- Android fisico en red local: `http://<IP_PC>:8000`
- Android fisico por USB con `adb reverse`: `http://127.0.0.1:8000`

## 3. Levantar el entorno

Desde la raiz del repositorio:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Si se quiere dejar corriendo en segundo plano:

```powershell
docker compose up -d --build
```

## 4. Verificar estado de contenedores

```powershell
docker compose ps
```

Todos los servicios principales deben figurar en estado `running`.

## 5. Health checks

### API gateway agregado

El endpoint principal de verificacion es:

- [http://localhost:8000/health](http://localhost:8000/health)

Este endpoint revisa:

- `parking-service`
- `face-service`
- `plate-service`
- `payment-service`
- `iot-service`
- PostgreSQL core
- PostgreSQL biometrico
- MinIO
- MQTT

Si todo esta bien, la respuesta debe incluir `status: "ok"`. Si algun componente falla, el gateway respondera `status: "degraded"` junto con el detalle del check afectado.

### Checks puntuales

- [http://localhost:8004/health](http://localhost:8004/health)
- [http://localhost:8005/health](http://localhost:8005/health)
- [http://localhost:8006/health](http://localhost:8006/health)
- [http://localhost:8007/health](http://localhost:8007/health)
- [http://localhost:8008/health](http://localhost:8008/health)

## 6. MinIO

Abrir la consola web:

- [http://localhost:9001](http://localhost:9001)

Credenciales por defecto:

- Usuario: `minioadmin`
- Clave: `minioadmin123`

Validaciones sugeridas:

- Confirmar que la consola carga.
- Confirmar que el servicio responde aun si no existen objetos todavia.

## 7. Node-RED

Abrir:

- Editor: [http://localhost:1880](http://localhost:1880)
- Dashboard demo: [http://localhost:1880/parking-dashboard](http://localhost:1880/parking-dashboard)

Validaciones sugeridas:

- Confirmar que el dashboard carga.
- Confirmar que los mensajes MQTT cambian universidad, campus, puerta, placa y ultimo evento.

## 8. Endpoint de prueba `POST /demo/open-gate`

El gateway expone una ruta de integracion rapida:

- `POST http://localhost:8000/demo/open-gate`

Payload:

```json
{
  "university_id": "uce",
  "campus_id": "matriz",
  "gate_id": "norte",
  "plate": "ABC1234"
}
```

Prueba manual desde PowerShell:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/demo/open-gate `
  -ContentType 'application/json' `
  -Body '{
    "university_id": "uce",
    "campus_id": "matriz",
    "gate_id": "norte",
    "plate": "ABC1234"
  }'
```

Comportamiento esperado:

- Registra un evento mock de demo.
- Publica MQTT en:
  `universities/uce/campuses/matriz/gates/norte/cmd`
- Retorna un JSON con `status: "OPEN_COMMAND_SENT"` y los topicos usados.

## 9. Flutter en Windows

Desde [mobile/app](C:\Users\damia\OneDrive\Documentos\parqueadero\mobile\app):

```powershell
flutter run -d windows --dart-define=API_BASE_URL=http://localhost:8000
```

Validaciones sugeridas:

- Iniciar sesion del operador.
- Entrar a `Demo IoT`.
- Presionar `Abrir barrera demo`.
- Confirmar respuesta exitosa en la app y reflejo en Node-RED.

## 10. Flutter en Android con `adb reverse`

Con el telefono conectado por USB y con depuracion habilitada:

```powershell
adb devices
adb reverse tcp:8000 tcp:8000
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

Validaciones sugeridas:

- Abrir la app en el telefono.
- Confirmar que el login ya no falla por conectividad.
- Navegar a `Demo IoT`.
- Presionar `Abrir barrera demo`.

## 11. Flutter en Android por Wi-Fi

Obtener la IP local del PC:

```powershell
ipconfig
```

Ejemplo:

```text
192.168.100.11
```

Luego ejecutar:

```powershell
flutter run --dart-define=API_BASE_URL=http://192.168.100.11:8000
```

## 12. Resultado esperado de integracion

La integracion local se considera satisfactoria cuando:

- `docker compose ps` muestra todos los servicios en ejecucion.
- `GET /health` del gateway responde con checks `ok` o permite identificar claramente el componente degradado.
- MinIO abre en `9001`.
- Node-RED abre en `1880` y muestra eventos MQTT.
- La app Flutter en Windows o Android llama al gateway en `8000`.
- El boton `Abrir barrera demo` genera publicacion MQTT y respuesta positiva en la app.
