# Admin Portal

## Objetivo

`/admin-portal` unifica en una sola SPA simple las vistas de:

- administracion del parqueadero
- secretaria / caja
- sesiones activas
- historial de salidas
- auditoria
- configuracion del gateway

La pagina usa HTML, CSS y JavaScript puro y se sirve desde `api-gateway`.

## URL de acceso

- Local: `http://localhost:8000/admin-portal`
- Red local: `http://IP_DE_TU_PC:8000/admin-portal`
- Externo: `http://IP_PUBLICA:8000/admin-portal`

## Secciones

### Dashboard

Consulta:

- sesiones activas
- vehiculos dentro
- pagos pendientes
- pagos realizados
- ingresos del dia
- salidas autorizadas
- salidas rechazadas

Endpoint:

- `GET /admin/dashboard-summary`

### Caja / Pagos

Permite:

- buscar una sesion activa por placa
- ver hora de entrada, tiempo estacionado, monto y estado
- registrar pago en secretaria
- ver monto congelado despues del pago
- ver hora de pago, validez y recibo

Endpoints:

- `GET /payments/by-plate/{plate_text}`
- `POST /payments/register-cash-payment`
- `POST /auth/token`

Notas:

- el portal puede abrirse sin login
- registrar pago sigue requiriendo autenticacion de caja o administracion
- toda la comunicacion pasa por `api-gateway`

### Sesiones activas

Muestra sesiones `INSIDE`.

Endpoint:

- `GET /admin/active-sessions`

### Historial

Muestra sesiones `OUTSIDE`.

Endpoint:

- `GET /admin/session-history`

### Auditoria

Muestra eventos recientes emitidos por los microservicios.

Endpoint:

- `GET /admin/audit-events`

### Configuracion

Permite cambiar `API_BASE_URL` y guardarlo en `localStorage`.

## Backend agregado

### API Gateway

Rutas nuevas:

- `POST /auth/token`
- `GET /auth/me`
- `GET /admin/dashboard-summary`
- `GET /admin/active-sessions`
- `GET /admin/session-history`
- `GET /admin/audit-events`
- `GET /admin-portal`
- `GET /admin-portal/styles.css`
- `GET /admin-portal/app.js`

### Payment Service

Rutas nuevas:

- `GET /payments/admin/dashboard-summary`
- `GET /payments/admin/active-sessions`
- `GET /payments/admin/session-history`

## Flujo recomendado

1. Abrir `http://localhost:8000/admin-portal`
2. Revisar `Dashboard`
3. Ir a `Caja / Pagos`
4. Iniciar sesion con usuario de caja si se necesita registrar pago
5. Buscar la placa
6. Registrar el pago
7. Confirmar que la sesion quede `PAID`
8. Verificar en `Historial` que la sesion desaparezca de activas despues de la salida

## Compatibilidad

- `web/cashier/` se mantiene como respaldo
- `web/admin-dashboard/` se mantiene como respaldo

## Seguridad

- el portal no expone datos biometricos completos
- la accion de registrar pago mantiene JWT y permisos
- las vistas de lectura estan pensadas para demostracion local y operacion interna

## Nuevas secciones para miembros

La SPA tambien incluye:

### Miembros

- alta de estudiante, docente o personal
- listado de miembros activos/inactivos

### Vehiculos

- registro de placa
- marca, modelo y color
- autorizacion de una persona para una placa

### Rostros

- subida de evidencia de rostro por archivo
- llamada a `/evidence/upload`
- enrolamiento posterior por `POST /members/{member_id}/faces/enroll`

### Permisos

- registro de permiso mensual
- asociacion `persona + vehiculo`
- rango de fechas, monto y metodo

## Endpoints nuevos usados por el portal

- `POST /members`
- `GET /members`
- `GET /members/{id}`
- `POST /vehicles`
- `GET /vehicles`
- `GET /vehicles/by-plate/{plate_text}`
- `POST /vehicles/{vehicle_id}/authorize-person`
- `GET /members/faces`
- `POST /members/{member_id}/faces/enroll`
- `GET /permits/monthly`
- `POST /permits/monthly`
- `GET /permits/by-plate/{plate_text}`
