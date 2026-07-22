-- Soporte para persistencia real de payment-service (antes 100% en
-- memoria en backend/services/payment-service/repositories/payment_repository.py).
--
-- payment-service no mantiene su propia tabla de sesiones: lee el estado
-- de la sesion (placa, hora de entrada/salida, tipo) directamente de
-- parking_sessions (ya migrada) y solo agrega su propia fila en `payments`
-- por cada intento/registro de pago.

-- 'not_required' es el estado que usa el flujo de miembros universitarios
-- (no visitantes) para indicar que no aplica cobro; el check constraint
-- original no lo contemplaba.
ALTER TABLE payments DROP CONSTRAINT IF EXISTS payments_payment_status_check;
ALTER TABLE payments ADD CONSTRAINT payments_payment_status_check
    CHECK (payment_status IN ('pending', 'paid', 'failed', 'cancelled', 'refunded', 'not_required'));

ALTER TABLE payments ADD COLUMN IF NOT EXISTS notes TEXT;

CREATE SEQUENCE IF NOT EXISTS payments_receipt_seq;
