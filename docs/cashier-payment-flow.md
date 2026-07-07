# Cashier Payment Flow

## Objetivo

Mover el pago del modo demo a un flujo operativo real para Secretaria/Caja:

1. El vehiculo entra y se crea una sesion `INSIDE`.
2. Para visitantes, la sesion queda con `payment_status=PENDING`.
3. Caja busca la sesion activa por placa.
4. Caja registra el pago.
5. El sistema cambia la sesion a `payment_status=PAID`.
6. En salida, `parking-service` solo autoriza si el estado ya es `PAID`.

## Estados

- `PENDING`: la sesion esta activa y aun no ha sido pagada.
- `PAID`: la sesion fue cobrada correctamente en Secretaria/Caja.
- `EXITED`: estado historico para sesiones ya cerradas en el servicio de pagos mock.

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
  "session_id": "session-visitor-pending-001",
  "plate_text": "VISPEND",
  "entry_time": "2026-07-07T19:25:00Z",
  "duration_minutes": 45,
  "amount": 1.5,
  "currency": "USD",
  "payment_status": "PENDING"
}
```

Notas:

- En `api-gateway` esta ruta queda disponible para consulta operativa local.
- Si no existe una sesion activa, responde `404`.

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
    "session_id": "session-visitor-pending-001",
    "plate_text": "VISPEND",
    "entry_time": "2026-07-07T19:25:00Z",
    "duration_minutes": 45,
    "amount": 1.5,
    "currency": "USD",
    "payment_status": "PAID"
  }
}
```

Validaciones:

- la sesion debe existir;
- la placa debe coincidir con la sesion;
- la sesion debe estar `INSIDE`;
- `payment_status` debe ser `PENDING`;
- el monto debe coincidir con la tarifa calculada;
- no se puede pagar dos veces la misma sesion.

## Regla en salida

`POST /parking/exit` conserva esta validacion:

- si `payment_status != PAID` -> `REJECTED`
- si `payment_status == PAID` -> `AUTHORIZED`

Esto aplica al flujo visitante. Para estudiantes, docentes y empleados se mantiene el comportamiento vigente basado en autorizacion y permisos.

## Pantalla web de Caja

Ruta local:

- [web/cashier/index.html](C:\Users\damia\OneDrive\Documentos\parqueadero\web\cashier\index.html)

Flujo:

1. Iniciar sesion con `cashier.user / demo1234!` o `admin.university / demo1234!`.
2. Buscar una placa activa.
3. Revisar tiempo y monto calculado.
4. Elegir metodo de pago.
5. Registrar pago.
6. Mostrar comprobante con `receipt_number`.

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

- `cashier_user_id`
- `plate_text`
- `amount`
- `payment_method`
- `notes`
- `receipt_number`

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
