# Cashier Payment Flow

## Objetivo

Mover el pago del modo demo a un flujo operativo real para Secretaria/Caja:

1. El vehiculo entra y se crea una sesion `INSIDE`.
2. Para visitantes, la sesion queda con `payment_status=PENDING`.
3. Caja busca la sesion activa por placa.
4. Caja registra el pago.
5. El sistema cambia la sesion a `payment_status=PAID`, guarda `paid_at`, `paid_amount`, `payment_method` y `receipt_number`.
6. El monto queda congelado y se calcula `payment_valid_until = paid_at + PAYMENT_GRACE_MINUTES`.
7. En salida, `parking-service` solo autoriza si el estado ya es `PAID` y el vehiculo sale dentro del tiempo de gracia.
8. Cuando el vehiculo sale, la sesion cambia a `OUTSIDE` y deja de aparecer como activa en Caja.

## Estados

- `INSIDE`: la sesion de parqueo sigue activa dentro del campus.
- `PENDING`: la sesion esta activa y aun no ha sido pagada.
- `PAID`: la sesion fue cobrada correctamente en Secretaria/Caja y el monto quedo congelado.
- `OUTSIDE`: el vehiculo ya salio y la sesion deja de considerarse activa para Caja.

## Roles

- `cashier`: puede consultar sesiones y registrar pagos.
- `admin_university`: puede consultar sesiones y registrar pagos.
- `gate_operator`: no puede marcar pagos; solo puede verificar si la sesion ya fue pagada.

## Endpoints

### `GET /payments/by-plate/{plate_text}`

Consulta la sesion activa `INSIDE` por placa.

Respuesta ejemplo:

```json
{
  "found": true,
  "message": "Sesion activa encontrada",
  "session_id": "session-visitor-pending-001",
  "plate_text": "VISPEND",
  "entry_time": "2026-07-07T19:25:00Z",
  "session_status": "INSIDE",
  "duration_minutes": 45,
  "amount": 1.5,
  "currency": "USD",
  "payment_status": "PENDING"
}
```

Notas:

- En `api-gateway` esta ruta queda disponible para consulta operativa local.
- Si no existe una sesion activa, responde `200` con:

```json
{
  "found": false,
  "message": "No active session found for this plate"
}
```
- Solo devuelve sesiones con `session_status=INSIDE`.
- Si la sesion ya fue pagada, devuelve el monto congelado en `paid_amount` y la validez en `payment_valid_until`.

### `POST /payments/register-cash-payment`

Registra el pago desde Caja.

Request:

```json
{
  "session_id": "session-visitor-pending-001",
  "plate_text": "VISPEND",
  "amount": 1.5,
  "payment_method": "cash",
  "cashier_user_id": "cashier.user",
  "notes": "Pago en secretaria"
}
```

Response:

```json
{
  "success": true,
  "message": "Cash payment registered successfully",
  "receipt_number": "REC-20260707-0002",
  "paid_at": "2026-07-07T20:10:31Z",
  "audit_log_id": "5f3f0fd6-3f0a-42f0-b5b8-e9d12f0e8e71",
  "session": {
    "found": true,
    "message": "Pago registrado",
    "session_id": "session-visitor-pending-001",
    "plate_text": "VISPEND",
    "entry_time": "2026-07-07T19:25:00Z",
    "session_status": "INSIDE",
    "duration_minutes": 45,
    "amount": 1.5,
    "currency": "USD",
    "payment_status": "PAID",
    "paid_at": "2026-07-07T20:10:31Z",
    "paid_amount": 1.5,
    "payment_method": "cash",
    "payment_valid_until": "2026-07-07T20:25:31Z",
    "receipt_number": "REC-20260707-0002"
  }
}
```

Validaciones:

- la sesion debe existir;
- la placa debe coincidir con la sesion;
- la sesion debe estar `INSIDE`;
- `payment_status` debe ser `PENDING`;
- el monto debe coincidir con la tarifa calculada;
- una vez pagada, no se recalcula el monto;
- se genera un tiempo de gracia configurable con `PAYMENT_GRACE_MINUTES`;
- no se puede pagar dos veces la misma sesion.

## Regla en salida

`POST /parking/exit` conserva esta validacion:

- si `payment_status != PAID` -> `REJECTED`
- si `payment_status == PAID` y sigue dentro de `payment_valid_until` -> `AUTHORIZED`
- si `payment_status == PAID` pero ya expiro el tiempo de gracia -> `REJECTED` con `Payment grace period expired`

Esto aplica al flujo visitante. Para estudiantes, docentes y empleados se mantiene el comportamiento vigente basado en autorizacion y permisos.

## Pantalla web de Caja

Ruta local:

- [web/cashier/index.html](C:\Users\damia\OneDrive\Documentos\parqueadero\web\cashier\index.html)

Flujo:

1. Iniciar sesion con `cashier.user / demo1234!` o `admin.university / demo1234!`.
2. Buscar una placa activa.
3. Si la sesion esta `PENDING`, revisar tiempo y monto calculado.
4. Elegir metodo de pago.
5. Registrar pago.
6. La pantalla refresca la sesion.
7. Si la sesion ya esta `PAID`, la pantalla muestra:
   - `Pago registrado`
   - `Monto pagado`
   - `Hora de pago`
   - `Valido hasta`
8. El boton `Registrar pago` queda deshabilitado mientras la sesion siga `PAID`.
9. Cuando el vehiculo sale y la sesion pasa a `OUTSIDE`, una nueva busqueda por placa devuelve `No hay sesion activa para esta placa`.

## Aplicacion Flutter

En la pantalla de salida:

- se elimina el flujo de "Marcar pago demo";
- el operador de puerta usa `Verificar pago`;
- la app solo consulta si la sesion ya fue pagada;
- el guardia no puede cambiar `payment_status` manualmente.

## Auditoria

Cada intento de cobro registra eventos de auditoria:

- `payment.cashier.completed`
- `payment.cashier.rejected`

Se guarda:

- `session_id`
- `cashier_user_id`
- `plate_text`
- `payment_status` antes y despues
- `session_status` antes y despues
- `amount`
- `paid_amount`
- `payment_method`
- `notes`
- `paid_at`
- `payment_valid_until`
- `receipt_number`
- `exit_time`

## Ejemplo rapido de uso

```bash
curl http://127.0.0.1:8000/payments/by-plate/VISPEND
```

Luego, con token JWT de `cashier.user` o `admin.university`:

```bash
curl -X POST http://127.0.0.1:8000/payments/register-cash-payment \
  -H "Authorization: Bearer TU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"session-visitor-pending-001\",\"plate_text\":\"VISPEND\",\"amount\":1.50,\"payment_method\":\"cash\",\"cashier_user_id\":\"cashier.user\",\"notes\":\"Pago en secretaria\"}"
```
