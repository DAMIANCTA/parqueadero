# Member Access Flow

## Objetivo

Separar claramente dos flujos de acceso vehicular:

- `VISITOR`: crea sesion temporal y paga por permanencia.
- `MEMBER`: usa placa registrada, rostro enrolado y permiso mensual vigente.

Esta fase mantiene intacto el flujo de visitantes y el flujo de Caja, pero agrega catalogo y validacion para estudiantes, docentes y personal administrativo.

## Reglas funcionales

### Visitantes

- siguen usando `POST /parking/entry` y `POST /parking/exit`;
- la sesion entra como `access_type=VISITOR`;
- `payment_status=PENDING` al ingresar;
- la salida solo se autoriza cuando `payment_status=PAID`.

### Miembros universitarios

- deben existir en `/members`;
- deben tener al menos una placa autorizada;
- deben tener un rostro enrolado;
- deben tener un permiso mensual vigente;
- no pagan por cada salida;
- la entrada y salida validan `placa + rostro + permiso`.

## Entidades

### Miembros

- `id`
- `university_id`
- `document_id`
- `institutional_id`
- `full_name`
- `email`
- `role_type`: `STUDENT | TEACHER | STAFF`
- `status`: `ACTIVE | INACTIVE`

### Vehiculos

- `id`
- `university_id`
- `plate_text`
- `brand`
- `model`
- `color`
- `status`

### Autorizaciones persona-vehiculo

- `id`
- `person_id`
- `vehicle_id`
- `is_owner`
- `status`

### Permisos mensuales

- `id`
- `person_id`
- `vehicle_id`
- `start_date`
- `end_date`
- `amount`
- `payment_method`
- `status`: `VALID | EXPIRED | SUSPENDED`
- `paid_at`
- `receipt_number`

### Perfiles faciales

- `id`
- `person_id`
- `face_image_id`
- `embedding_id`
- `template_id`
- `provider`
- `status`

## Servicios involucrados

### `vehicle-service`

Es el propietario del catalogo de miembros universitarios:

- miembros
- vehiculos
- autorizaciones persona-vehiculo
- permisos mensuales
- perfiles faciales enrolados
- validacion de acceso de miembro

### `parking-service`

Mantiene la logica operativa de puerta:

- decide si una placa entra por flujo `MEMBER` o `VISITOR`;
- crea y cierra sesiones;
- llama a IoT para abrir barrera;
- registra auditoria y eventos.

### `face-service`

Se usa para:

- enrolar rostro del miembro;
- comparar la captura actual con el rostro registrado.

### `payment-service`

Se mantiene para visitantes y tambien refleja sesiones `NOT_REQUIRED` de miembros, con monto `0.00`, para que el portal administrativo las vea sin intentar cobrarlas.

## Endpoints de miembros

### Catalogo

- `POST /members`
- `GET /members`
- `GET /members/{id}`
- `POST /vehicles`
- `GET /vehicles`
- `GET /vehicles/by-plate/{plate_text}`
- `POST /vehicles/{vehicle_id}/authorize-person`

### Rostros

- `POST /members/{member_id}/faces/enroll`
- `GET /members/faces`

### Permisos mensuales

- `POST /permits/monthly`
- `GET /permits/monthly`
- `GET /permits/by-plate/{plate_text}`

### Validacion operativa

- `POST /access/validate-member-entry`

Para integracion interna entre servicios tambien existen:

- `POST /internal/access/validate-member-entry`
- `POST /internal/access/validate-member-exit`
- `GET /internal/vehicles/by-plate/{plate_text}`

## Flujo de entrada MEMBER

1. La app o dispositivo captura la placa y el rostro.
2. `parking-service` normaliza la placa.
3. `parking-service` consulta si la placa existe como vehiculo registrado.
4. Si la placa existe:
   - llama a `vehicle-service`;
   - compara el rostro capturado contra las personas autorizadas para esa placa;
   - verifica si hay permiso mensual vigente.
5. Si todo coincide:
   - crea sesion con `access_type=MEMBER`;
   - asigna `payment_status=NOT_REQUIRED`;
   - guarda `person_id`, `person_name`, `role_type` y `vehicle_id`;
   - publica apertura de barrera.
6. Si la placa no existe como miembro registrado:
   - cae al flujo visitante.
7. Si la placa existe pero el rostro o permiso fallan:
   - rechaza el acceso;
   - no cae a visitante.

## Flujo de salida MEMBER

1. Se busca la sesion activa por placa.
2. Si la sesion es `MEMBER`:
   - no se exige pago por salida;
   - se valida rostro contra la persona registrada en la sesion o las personas autorizadas;
   - se verifica que el permiso siga vigente.
3. Si todo es valido:
   - la sesion cambia a `OUTSIDE`;
   - se abre la barrera;
   - se registra auditoria.
4. Si falla rostro o permiso:
   - `REJECTED`.

## Flujo de enrolamiento facial

1. El portal administrativo sube una imagen de rostro a `POST /evidence/upload`.
2. La evidencia queda en MinIO y la base guarda solo la referencia.
3. El portal llama `POST /members/{member_id}/faces/enroll` con `face_image_id`.
4. `vehicle-service` busca la referencia en `postgres-biometrics`.
5. `vehicle-service` llama a `face-service /faces/enroll`.
6. Se registra `face_profile` enlazado al miembro.

## Portal administrativo

La SPA `web/admin-portal/` ahora incluye secciones para:

- `Miembros`
- `Vehiculos`
- `Rostros`
- `Permisos`

Todas consumen siempre el `api-gateway`.

## Roles recomendados

- `admin_university`:
  - registrar miembros
  - registrar vehiculos
  - autorizar placas
  - enrolar rostros
  - registrar permisos mensuales

- `cashier`:
  - registrar pagos de visitantes
  - registrar permisos mensuales

- `security` y `gate_operator`:
  - usar `parking/entry`
  - usar `parking/exit`
  - no crear catalogo administrativo

- `auditor`:
  - consultar informacion operativa y auditoria

## Notas de esta fase

- las fotos no se guardan en PostgreSQL;
- MinIO conserva los objetos;
- `postgres-biometrics` guarda referencias y templates;
- el flujo visitante y Caja sigue activo;
- `plate-service` no se modifica.
