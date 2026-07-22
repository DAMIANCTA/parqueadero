-- Soporte para el rol DRIVER (conductores auto-registrados desde la app
-- movil del conductor) y persistencia real de permisos mensuales, perfiles
-- de rostro (indice, no biometria) y sesiones/eventos de garita.
--
-- Antes de esta migracion, auth-service, vehicle-service, parking-service y
-- payment-service guardaban estos datos solo en memoria del proceso Python
-- (se perdian en cada reinicio de contenedor). Este archivo amplia el
-- esquema para que ese codigo pueda escribir contra Postgres real sin
-- perder ninguna de las formas de dato que ya usaba.

-- 1) Permitir 'driver' como person_type (antes solo student/teacher/
--    employee/visitor/contractor/security).
ALTER TABLE persons DROP CONSTRAINT IF EXISTS persons_person_type_check;
ALTER TABLE persons ADD CONSTRAINT persons_person_type_check
    CHECK (person_type IN ('student', 'teacher', 'employee', 'visitor', 'contractor', 'security', 'driver'));

-- 2) Rol 'driver' para inicio de sesion/permisos de las cuentas de
--    conductor auto-registradas.
INSERT INTO roles (id, role_key, display_name, description, status)
VALUES (
    '44444444-4444-4444-4444-444444444412',
    'driver',
    'Conductor',
    'Conductor auto-registrado desde la app movil, dueno de su propio vehiculo.',
    'active'
)
ON CONFLICT (role_key) DO NOTHING;

-- 3) Permisos mensuales de vehiculo (antes en memoria en
--    vehicle-service/repositories/member_repository.py::create_monthly_permit).
CREATE SEQUENCE IF NOT EXISTS monthly_permits_receipt_seq;

CREATE TABLE IF NOT EXISTS monthly_permits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    person_id UUID NOT NULL REFERENCES persons(id) ON DELETE RESTRICT,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    amount NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (amount >= 0),
    payment_method VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'VALID'
        CHECK (status IN ('VALID', 'EXPIRED', 'SUSPENDED')),
    paid_at TIMESTAMPTZ,
    receipt_number VARCHAR(40) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_monthly_permits_university_id ON monthly_permits (university_id);
CREATE INDEX IF NOT EXISTS idx_monthly_permits_person_id ON monthly_permits (person_id);
CREATE INDEX IF NOT EXISTS idx_monthly_permits_vehicle_id ON monthly_permits (vehicle_id);
CREATE INDEX IF NOT EXISTS idx_monthly_permits_status ON monthly_permits (status);

DROP TRIGGER IF EXISTS trg_monthly_permits_updated_at ON monthly_permits;
CREATE TRIGGER trg_monthly_permits_updated_at
BEFORE UPDATE ON monthly_permits
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- 4) Indice de perfiles de rostro por persona (antes en memoria en
--    member_repository.py::create_face_profile). La biometria real
--    (embeddings) vive en postgres-biometrics (face_templates); esta tabla
--    solo indexa "esta persona tiene un rostro enrolado y donde" para que
--    vehicle-service no duplique ese trabajo. Sin FK entre bases distintas.
CREATE TABLE IF NOT EXISTS face_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    person_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    face_image_id UUID NOT NULL,
    template_id UUID,
    embedding_id UUID,
    provider VARCHAR(60) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'INACTIVE')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_face_profiles_university_id ON face_profiles (university_id);
CREATE INDEX IF NOT EXISTS idx_face_profiles_person_id ON face_profiles (person_id);
CREATE INDEX IF NOT EXISTS idx_face_profiles_status ON face_profiles (status);

DROP TRIGGER IF EXISTS trg_face_profiles_updated_at ON face_profiles;
CREATE TRIGGER trg_face_profiles_updated_at
BEFORE UPDATE ON face_profiles
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- 5) Columnas denormalizadas que parking-service ya necesitaba en su
--    representacion en memoria de una sesion (persona/rostro de
--    entrada-salida), y que la tabla real no tenia todavia.
ALTER TABLE parking_sessions ADD COLUMN IF NOT EXISTS person_name TEXT;
ALTER TABLE parking_sessions ADD COLUMN IF NOT EXISTS person_type VARCHAR(30);
ALTER TABLE parking_sessions ADD COLUMN IF NOT EXISTS role_type VARCHAR(30);
ALTER TABLE parking_sessions ADD COLUMN IF NOT EXISTS entry_face_evidence_id UUID;
ALTER TABLE parking_sessions ADD COLUMN IF NOT EXISTS entry_plate_evidence_id UUID;
ALTER TABLE parking_sessions ADD COLUMN IF NOT EXISTS exit_face_evidence_id UUID;
ALTER TABLE parking_sessions ADD COLUMN IF NOT EXISTS exit_plate_evidence_id UUID;

-- 6) Puerta por defecto para el flujo fisico de garita (garita-controller
--    manda hoy un gate_id de texto libre, ej. "garita-01", que
--    parking-service debe resolver contra esta tabla por "code").
INSERT INTO gates (id, university_id, campus_id, name, code, direction_type, status)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    'Garita Fisica',
    'GARITA01',
    'bidirectional',
    'active'
)
ON CONFLICT (campus_id, code) DO NOTHING;

-- 7) Campos que auth-service necesita y el esquema real todavia no tenia:
--    universities.city (usado por UniversityResponse/UniversityCreateRequest)
--    y users.document_number/phone (cuenta de conductor auto-registrado).
ALTER TABLE universities ADD COLUMN IF NOT EXISTS city VARCHAR(120) NOT NULL DEFAULT 'Quito';
ALTER TABLE users ADD COLUMN IF NOT EXISTS document_number VARCHAR(30);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
