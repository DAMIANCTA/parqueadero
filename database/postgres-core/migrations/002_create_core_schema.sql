CREATE TABLE IF NOT EXISTS universities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(160) NOT NULL,
    code VARCHAR(50) NOT NULL,
    legal_name VARCHAR(200),
    country_code VARCHAR(10) DEFAULT 'EC',
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_universities_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS campuses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    name VARCHAR(160) NOT NULL,
    code VARCHAR(50) NOT NULL,
    address_line TEXT,
    city VARCHAR(120),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_campuses_university_code UNIQUE (university_id, code)
);

CREATE TABLE IF NOT EXISTS gates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    campus_id UUID NOT NULL REFERENCES campuses(id) ON DELETE RESTRICT,
    name VARCHAR(160) NOT NULL,
    code VARCHAR(50) NOT NULL,
    direction_type VARCHAR(20) NOT NULL DEFAULT 'bidirectional'
        CHECK (direction_type IN ('entry', 'exit', 'bidirectional')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_gates_university_code UNIQUE (university_id, code),
    CONSTRAINT uq_gates_campus_code UNIQUE (campus_id, code)
);

CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    campus_id UUID REFERENCES campuses(id) ON DELETE SET NULL,
    gate_id UUID REFERENCES gates(id) ON DELETE SET NULL,
    device_code VARCHAR(80) NOT NULL,
    device_name VARCHAR(160) NOT NULL,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('android', 'ios', 'web', 'embedded')),
    device_type VARCHAR(30) NOT NULL DEFAULT 'mobile_camera'
        CHECK (device_type IN ('mobile_camera', 'gate_controller', 'manual_console', 'sensor')),
    last_seen_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_devices_university_code UNIQUE (university_id, device_code)
);

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_key VARCHAR(60) NOT NULL,
    display_name VARCHAR(120) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_roles_role_key UNIQUE (role_key)
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID REFERENCES universities(id) ON DELETE SET NULL,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    username VARCHAR(80) NOT NULL,
    email VARCHAR(180),
    password_hash TEXT NOT NULL,
    first_name VARCHAR(120),
    last_name VARCHAR(120),
    last_login_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE SET NULL,
    campus_id UUID REFERENCES campuses(id) ON DELETE SET NULL,
    institutional_code VARCHAR(80),
    full_name VARCHAR(180) NOT NULL,
    document_number VARCHAR(50),
    email VARCHAR(180),
    phone VARCHAR(40),
    person_type VARCHAR(30) NOT NULL
        CHECK (person_type IN ('student', 'teacher', 'employee', 'visitor', 'contractor', 'security')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_persons_university_institutional_code UNIQUE (university_id, institutional_code),
    CONSTRAINT uq_persons_university_document_number UNIQUE (university_id, document_number)
);

CREATE TABLE IF NOT EXISTS vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    owner_person_id UUID REFERENCES persons(id) ON DELETE SET NULL,
    plate VARCHAR(20) NOT NULL,
    vehicle_type VARCHAR(30) NOT NULL DEFAULT 'car'
        CHECK (vehicle_type IN ('car', 'motorcycle', 'truck', 'van', 'other')),
    brand VARCHAR(80),
    model VARCHAR(80),
    color VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_vehicles_university_plate UNIQUE (university_id, plate)
);

CREATE TABLE IF NOT EXISTS vehicle_authorizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES persons(id) ON DELETE RESTRICT,
    authorization_type VARCHAR(30) NOT NULL DEFAULT 'owner'
        CHECK (authorization_type IN ('owner', 'primary_driver', 'authorized_driver', 'temporary_driver')),
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ,
    notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_vehicle_authorizations_scope UNIQUE (university_id, vehicle_id, person_id, authorization_type)
);

CREATE TABLE IF NOT EXISTS parking_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    campus_id UUID NOT NULL REFERENCES campuses(id) ON DELETE RESTRICT,
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE SET NULL,
    person_id UUID REFERENCES persons(id) ON DELETE SET NULL,
    entry_gate_id UUID NOT NULL REFERENCES gates(id) ON DELETE RESTRICT,
    exit_gate_id UUID REFERENCES gates(id) ON DELETE SET NULL,
    entry_device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
    exit_device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
    session_type VARCHAR(20) NOT NULL CHECK (session_type IN ('visitor', 'internal')),
    session_status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (session_status IN ('open', 'closed', 'cancelled', 'rejected')),
    detected_plate VARCHAR(20),
    payment_required BOOLEAN NOT NULL DEFAULT FALSE,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (payment_status IN ('pending', 'paid', 'failed', 'waived', 'not_required')),
    entry_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exit_time TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    parking_session_id UUID NOT NULL REFERENCES parking_sessions(id) ON DELETE CASCADE,
    collected_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reference_code VARCHAR(80),
    amount NUMERIC(10, 2) NOT NULL CHECK (amount >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    payment_method VARCHAR(30) NOT NULL
        CHECK (payment_method IN ('cash', 'card', 'transfer', 'mobile', 'online', 'other')),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (payment_status IN ('pending', 'paid', 'failed', 'cancelled', 'refunded')),
    paid_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_payments_reference_code UNIQUE (reference_code)
);

CREATE TABLE IF NOT EXISTS access_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    parking_session_id UUID REFERENCES parking_sessions(id) ON DELETE SET NULL,
    gate_id UUID REFERENCES gates(id) ON DELETE SET NULL,
    device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
    person_id UUID REFERENCES persons(id) ON DELETE SET NULL,
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE SET NULL,
    operator_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(30) NOT NULL
        CHECK (event_type IN (
            'entry_attempt',
            'entry_granted',
            'entry_denied',
            'exit_attempt',
            'exit_granted',
            'exit_denied',
            'manual_override'
        )),
    result VARCHAR(20) NOT NULL CHECK (result IN ('success', 'denied', 'error', 'warning')),
    reason TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL REFERENCES universities(id) ON DELETE RESTRICT,
    campus_id UUID REFERENCES campuses(id) ON DELETE SET NULL,
    gate_id UUID REFERENCES gates(id) ON DELETE SET NULL,
    parking_session_id UUID REFERENCES parking_sessions(id) ON DELETE SET NULL,
    reported_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    incident_type VARCHAR(40) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium'
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    incident_status VARCHAR(20) NOT NULL DEFAULT 'open'
        CHECK (incident_status IN ('open', 'in_progress', 'resolved', 'closed')),
    description TEXT NOT NULL,
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID REFERENCES universities(id) ON DELETE SET NULL,
    actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    actor_role_key VARCHAR(60),
    action VARCHAR(120) NOT NULL,
    resource_type VARCHAR(80) NOT NULL,
    resource_id UUID,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    ip_address INET,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
