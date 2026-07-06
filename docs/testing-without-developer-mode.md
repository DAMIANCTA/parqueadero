# Pruebas Sin Modo Desarrollador

## Objetivo

Este documento describe como probar Smart Parking University sin depender del modo desarrollador del telefono. El enfoque contempla tres escenarios:

1. Prueba local desde Windows con Flutter Desktop.
2. Prueba desde un telefono Android con APK release instalado manualmente.
3. Prueba desde navegador usando Node-RED desde otro dispositivo en la misma red.

## 1. Obtener la IP local de la PC

Desde PowerShell:

```powershell
ipconfig
```

Busque la `Direccion IPv4` de la interfaz conectada a la misma red Wi-Fi o Ethernet. Por ejemplo:

```text
192.168.100.11
```

En este documento se usara `192.168.100.11` como ejemplo. Sustituya ese valor por la IP real de su equipo.

## 2. Verificar servicios base

Levantar el proyecto:

```powershell
cd C:\Users\damia\OneDrive\Documentos\parqueadero
docker compose up -d --build
```

Revisar contenedores:

```powershell
docker compose ps
```

### Health principal

El punto unico de salud es el `api-gateway`:

- [http://localhost:8000/health](http://localhost:8000/health)

Desde otro dispositivo en la misma red:

- `http://192.168.100.11:8000/health`

El health del gateway comprueba:

- `parking-service`
- `face-service`
- `plate-service`
- `payment-service`
- `iot-service`
- PostgreSQL core
- PostgreSQL biometrico
- MinIO
- MQTT

## 3. Prueba local desde Windows

La app de escritorio ya incluye el flujo de prueba `Demo IoT` con el boton **Abrir barrera demo**.

### Ejecutar

```powershell
cd C:\Users\damia\OneDrive\Documentos\parqueadero\mobile\app
flutter run -d windows --dart-define=API_BASE_URL=http://localhost:8000
```

### Probar

1. Abrir la app.
2. En login, verificar que `API base URL` sea `http://localhost:8000`.
3. Iniciar sesion.
4. Entrar a `Demo IoT`.
5. Presionar `Abrir barrera demo`.
6. Confirmar que la app muestre la respuesta del backend:
   - estado
   - mensaje
   - topico MQTT
   - evento demo

## 4. Probar `POST /demo/open-gate`

Desde PowerShell:

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

Respuesta esperada:

- `status: "OPEN_COMMAND_SENT"`
- `topic: "universities/uce/campuses/matriz/gates/norte/cmd"`
- `published: true`

## 5. Probar desde celular sin modo desarrollador

### Idea general

No se requiere modo desarrollador para usar la app ya instalada. Se necesita un APK release y que el telefono y la PC esten en la misma red.

La app ya incluye un campo `API base URL` en el login. Esto permite cambiar la direccion del backend sin recompilar cada vez y evita el uso de `localhost` en Android instalado.

### API base URL recomendada

Usar la IP local de la PC:

```text
http://192.168.100.11:8000
```

### Generar APK release

Desde:

```powershell
cd C:\Users\damia\OneDrive\Documentos\parqueadero\mobile\app
```

Construir:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=http://192.168.100.11:8000
```

APK generado en:

[app-release.apk](/C:/Users/damia/OneDrive/Documentos/parqueadero/mobile/app/build/app/outputs/flutter-apk/app-release.apk)

### Instalar sin modo desarrollador

1. Copiar el APK al telefono por cable, WhatsApp, Drive o correo.
2. Abrir el archivo APK en el telefono.
3. Permitir `Instalar apps desconocidas` para la aplicacion desde la que se abre el APK.
4. Instalar la app.

No es necesario activar `USB debugging` ni `Developer mode` para ejecutar la app ya instalada.

### Probar en el telefono

1. Abrir la app.
2. En el login, revisar el campo `API base URL`.
3. Si hace falta, escribir:

```text
http://192.168.100.11:8000
```

4. Iniciar sesion.
5. Entrar a `Demo IoT`.
6. Presionar `Abrir barrera demo`.
7. Verificar que aparezca la respuesta positiva.

## 6. Probar Node-RED desde otro dispositivo

Node-RED queda expuesto en toda la red local por el puerto `1880`.

Abrir desde la PC:

- [http://localhost:1880](http://localhost:1880)
- [http://localhost:1880/parking-dashboard](http://localhost:1880/parking-dashboard)

Abrir desde el telefono u otra PC en la misma red:

- `http://192.168.100.11:1880`
- `http://192.168.100.11:1880/parking-dashboard`

Uso esperado:

- visualizar universidad
- campus
- puerta
- placa
- estado de barrera
- motivo
- ultimo evento

## 7. MinIO desde otro dispositivo

Si se quiere ver la consola desde otro equipo en la misma red:

- `http://192.168.100.11:9001`

Credenciales por defecto:

- usuario: `minioadmin`
- clave: `minioadmin123`

## 8. CORS para pruebas web y origenes locales

El `api-gateway` ya incluye `CORSMiddleware` para permitir pruebas desde Flutter Web u otros origenes locales.

Variable actual:

```text
CORS_ALLOW_ORIGINS=*
```

En entornos productivos se recomienda restringirla a dominios y origenes especificos.

## 9. Puertos que deben estar permitidos en el firewall

Para pruebas locales con otros dispositivos en la misma red, permitir entrada en:

- `8000` -> API gateway
- `1880` -> Node-RED
- `9001` -> MinIO Console

Opcionales segun necesidad:

- `9000` -> MinIO API
- `1883` -> MQTT
- `9002` -> MQTT WebSocket

Si la app movil no logra conectarse, la causa mas frecuente es que Windows Defender Firewall este bloqueando el puerto `8000`.

## 10. Checklist de validacion

1. `docker compose ps`
2. Abrir `http://localhost:8000/health`
3. Abrir `http://192.168.100.11:8000/health` desde otro dispositivo
4. Ejecutar `POST /demo/open-gate`
5. Abrir `http://192.168.100.11:1880/parking-dashboard`
6. Instalar APK release
7. Configurar `API base URL` en la app movil
8. Presionar `Abrir barrera demo`

## 11. Demo completa sin modo desarrollador

Para demostrar el flujo funcional sin conectar el telefono por USB:

1. Instalar el APK release.
2. En el login, configurar `API base URL` con la IP local del PC, por ejemplo:

```text
http://192.168.100.11:8000
```

3. Iniciar sesion y seleccionar puerta.
4. En `Modo entrada`, registrar una placa visitante como `VIS1001` con rostro y liveness validos.
5. Desde otro navegador en el telefono o en otra PC, abrir:

```text
http://192.168.100.11:1880/parking-dashboard
```

6. Verificar que Node-RED muestre:
   - `entry`
   - `authorized`
   - la placa
   - barrera abierta
7. En `Modo salida`, intentar salir con la misma placa sin pagar.
8. Confirmar que la app rechaza la salida y que Node-RED muestre:
   - `exit`
   - `rejected`
   - `payment_pending`
   - barrera cerrada
9. Presionar `Marcar pago demo`.
10. Reintentar `Validar salida`.
11. Confirmar salida autorizada y barrera abierta.
