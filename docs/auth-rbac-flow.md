# Auth, RBAC y Multiuniversidad

## Objetivo

El portal administrativo y los endpoints administrativos del sistema Smart Parking University usan autenticacion JWT y control de acceso por roles. La preparacion multiuniversidad se aplica mediante `university_id` en el token y filtros de alcance en el API Gateway.

## Flujo de login

1. El portal llama a `POST /auth/login` en el API Gateway.
2. El API Gateway reenvia la solicitud a `auth-service`.
3. `auth-service` valida usuario y password hash.
4. Si las credenciales son correctas, responde:
   - `access_token`
   - `token_type`
   - `expires_in`
   - `roles`
   - `permissions`
   - `university_id`
   - `user`
5. El portal guarda el token y el usuario en `localStorage`.
6. Las llamadas administrativas posteriores envian `Authorization: Bearer <token>`.

## Roles soportados

- `SUPER_ADMIN`
  - acceso total
  - puede crear universidades
  - puede crear usuarios para cualquier universidad
  - puede ver todo el sistema

- `UNIVERSITY_ADMIN`
  - administracion completa solo dentro de su universidad
  - puede ver dashboard, pagos, auditoria, garitas, miembros, vehiculos, permisos y usuarios internos

- `CASHIER`
  - caja y pagos
  - consulta sesiones activas por placa
  - registra pagos de visitantes
  - consulta historial

- `MEMBER_MANAGER`
  - miembros universitarios
  - vehiculos autorizados
  - permisos mensuales
  - enrolamiento de rostros

- `SECURITY`
  - sesiones activas
  - historial operativo
  - garitas e IoT
  - apertura o denegacion manual si su rol lo permite

- `AUDITOR`
  - solo lectura
  - dashboard
  - historial
  - auditoria

## Matriz de permisos

- `dashboard.read`: dashboard del portal
- `sessions.read`: sesiones activas
- `history.read`: historial de sesiones y pagos
- `audit.read`: auditoria
- `universities.read`, `universities.write`: catalogo de universidades
- `users.read`, `users.write`: usuarios internos
- `members.read`, `members.write`: miembros universitarios
- `vehicles.read`, `vehicles.write`: vehiculos y autorizaciones
- `permits.read`, `permits.write`: permisos mensuales
- `faces.read`, `faces.enroll`, `faces.verify`, `faces.compare`, `faces.liveness_check`: rostro
- `payments.read`, `payments.pay`: caja y pagos
- `iot.gates.read`, `iot.gates.open`, `iot.gates.deny`: garitas
- `plates.detect`: deteccion de placa

## Multiuniversidad

### Regla general

- `SUPER_ADMIN` puede trabajar con cualquier universidad.
- El resto de roles queda restringido al `university_id` de su token.
- El API Gateway resuelve el alcance y bloquea accesos cruzados antes de reenviar a los microservicios.

### Endpoints con alcance

- `GET /users`
- `POST /users`
- `GET /universities`
- `POST /universities`
- `GET /members`
- `POST /members`
- `GET /vehicles`
- `POST /vehicles`
- `GET /permits/monthly`
- `POST /permits/monthly`
- `GET /payments/by-plate/{plate}`
- `GET /admin/dashboard-summary`
- `GET /admin/active-sessions`
- `GET /admin/session-history`

## Usuarios demo

- `super.admin` / `demo1234!` -> `SUPER_ADMIN`
- `admin.university` / `demo1234!` -> `UNIVERSITY_ADMIN`
- `cashier.uce` / `demo1234!` -> `CASHIER`
- `members.uce` / `demo1234!` -> `MEMBER_MANAGER`
- `security.uce` / `demo1234!` -> `SECURITY`
- `auditor.uce` / `demo1234!` -> `AUDITOR`

Compatibilidad operativa:

- `cashier.user` / `demo1234!`
- `gate.operator` / `demo1234!`
- `security.agent` / `demo1234!`

## Seguridad aplicada

- passwords almacenadas con hash derivado por `pbkdf2_hmac`
- JWT firmado con `JWT_SECRET_KEY`
- expiracion configurable con `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`
- los endpoints administrativos del API Gateway ya no son publicos
- el portal filtra menu por rol y tambien evita llamar endpoints no permitidos
- el backend sigue siendo la fuente final de autorizacion

## Como probar

1. Iniciar sesion en `http://localhost:8000/admin-portal`.
2. Probar como `super.admin` y verificar:
   - menu completo
   - secciones `Usuarios` y `Universidades`
3. Probar como `cashier.uce` y verificar:
   - solo `Caja / Pagos` e `Historial`
   - puede registrar pago
   - no ve miembros ni usuarios
4. Probar como `members.uce` y verificar:
   - miembros, vehiculos, permisos y rostros
   - no puede registrar pagos
5. Probar como `auditor.uce` y verificar:
   - lectura de dashboard, historial y auditoria
   - no puede crear registros
