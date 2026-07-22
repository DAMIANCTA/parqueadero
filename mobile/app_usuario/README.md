# UCEPark - App del conductor

App React Native (Expo) para el conductor final del sistema de parqueo UCE.
Distinta de `mobile/app` (la app Flutter que usa el personal de seguridad
en la garita) — esta la usa el conductor para registrarse, ver su vehiculo,
su estado (dentro/fuera) y su historial de ingresos/salidas.

## Pantallas

- **Login / Registro**: contra el backend real (`POST /auth/login`,
  `POST /auth/register` en el api-gateway).
- **Inicio, Historial, Mi Perfil**: datos reales (`/vehicles/mine`,
  `/vehicles/mine/authorized-drivers`, `/parking/mine/active-session`,
  `/parking/mine/history`).
- **Conductores Autorizados**: lista real de solo lectura (mismo endpoint
  que usa Inicio); agregar/quitar conductores todavia no esta implementado
  (muestra "Proximamente").
- **Notificaciones**: pantalla de ejemplo con datos fijos — no existe
  todavia un backend de notificaciones.

## Correr la app

1. Copia `.env.example` a `.env` y pon la IP de LAN de tu PC (donde corre
   `docker compose` con el api-gateway en el puerto 8000), por ejemplo:
   ```
   EXPO_PUBLIC_API_BASE_URL=http://192.168.1.184:8000
   ```
   No uses `localhost` — el celular no puede resolver eso a tu PC.
2. `npm install` (si no lo hiciste ya).
3. `npx expo start` y escanea el QR con la app **Expo Go** en tu telefono
   (mismo WiFi que la PC).
4. Asegurate de que el backend este arriba: `docker compose up -d` desde
   la raiz del repo.

## Estructura

```
src/
  theme/        paleta y tipografia (Montserrat), iguales a las de mobile/app
  services/     apiClient.ts - llamadas al api-gateway
  context/      AuthContext - token, usuario, login/register/logout
  navigation/   RootNavigator (auth vs app) + TabsNavigator (Inicio/Historial/Perfil)
  components/   ui.tsx - tarjetas, botones, campos, chips de placa, etc.
  screens/      una pantalla por archivo
```
