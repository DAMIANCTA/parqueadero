-- Usuarios temporales de visitantes.
--
-- Se crea un registro por cada visitante NO registrado que ingresa al
-- parqueadero: al detectar la placa sin dueno asociado, la persona pone su
-- rostro y se genera este "usuario temporal", conservando sus datos.
--
-- El registro se retiene durante una ventana (por defecto 30 dias) para poder
-- consultarlo ante inconsistencias en la salida (por ejemplo, cuando el rostro
-- de salida no coincide con el de entrada y el guardia debe verificar por placa
-- quien habia ingresado). El backend aplica la caducidad con expires_at.

CREATE TABLE IF NOT EXISTS temporary_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    plate VARCHAR(20) NOT NULL,
    full_name VARCHAR(180),
    person_type VARCHAR(30) NOT NULL DEFAULT 'visitor'
        CHECK (person_type IN ('visitor')),
    -- Referencias cruzadas a la BD biometrica (sin FK entre bases distintas).
    face_template_id UUID,
    entry_face_evidence_id UUID,
    entry_plate_evidence_id UUID,
    entry_session_id UUID,
    entry_gate_id UUID,
    face_model_name VARCHAR(120),
    liveness_score NUMERIC(5, 4)
        CHECK (liveness_score IS NULL OR (liveness_score >= 0 AND liveness_score <= 1)),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'expired', 'converted', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Salvaguarda a nivel de BD; el backend fija expires_at explicitamente
    -- segun TEMP_USER_RETENTION_DAYS.
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '30 days')
);

CREATE INDEX IF NOT EXISTS idx_temporary_users_university_id ON temporary_users (university_id);
CREATE INDEX IF NOT EXISTS idx_temporary_users_plate ON temporary_users (plate);
CREATE INDEX IF NOT EXISTS idx_temporary_users_status ON temporary_users (status);
CREATE INDEX IF NOT EXISTS idx_temporary_users_expires_at ON temporary_users (expires_at);
CREATE INDEX IF NOT EXISTS idx_temporary_users_entry_session_id ON temporary_users (entry_session_id);

DROP TRIGGER IF EXISTS trg_temporary_users_updated_at ON temporary_users;
CREATE TRIGGER trg_temporary_users_updated_at
BEFORE UPDATE ON temporary_users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
