INSERT INTO universities (id, name, code, legal_name, country_code, status)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'Universidad Demo Smart Parking',
    'UDSP',
    'Universidad Demo Smart Parking S.A.',
    'EC',
    'active'
)
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    legal_name = EXCLUDED.legal_name,
    country_code = EXCLUDED.country_code,
    status = EXCLUDED.status,
    updated_at = NOW();

INSERT INTO campuses (id, university_id, name, code, address_line, city, status)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'Campus Central',
    'CENTRAL',
    'Av. Universidad 100',
    'Quito',
    'active'
)
ON CONFLICT (university_id, code) DO UPDATE
SET
    name = EXCLUDED.name,
    address_line = EXCLUDED.address_line,
    city = EXCLUDED.city,
    status = EXCLUDED.status,
    updated_at = NOW();

INSERT INTO gates (id, university_id, campus_id, name, code, direction_type, status)
VALUES
    (
        '33333333-3333-3333-3333-333333333331',
        '11111111-1111-1111-1111-111111111111',
        '22222222-2222-2222-2222-222222222222',
        'Puerta Norte',
        'NORTE',
        'bidirectional',
        'active'
    ),
    (
        '33333333-3333-3333-3333-333333333332',
        '11111111-1111-1111-1111-111111111111',
        '22222222-2222-2222-2222-222222222222',
        'Puerta Sur',
        'SUR',
        'bidirectional',
        'active'
    )
ON CONFLICT (campus_id, code) DO UPDATE
SET
    name = EXCLUDED.name,
    direction_type = EXCLUDED.direction_type,
    status = EXCLUDED.status,
    updated_at = NOW();

INSERT INTO roles (id, role_key, display_name, description, status)
VALUES
    ('44444444-4444-4444-4444-444444444401', 'superadmin', 'Super Administrador', 'Acceso total a toda la plataforma.', 'active'),
    ('44444444-4444-4444-4444-444444444402', 'admin_university', 'Administrador de Universidad', 'Gestiona configuracion y catalogos de una universidad.', 'active'),
    ('44444444-4444-4444-4444-444444444403', 'security', 'Seguridad', 'Monitorea accesos y eventos operativos.', 'active'),
    ('44444444-4444-4444-4444-444444444404', 'cashier', 'Cajero', 'Gestiona cobros y validaciones de pago.', 'active'),
    ('44444444-4444-4444-4444-444444444405', 'gate_operator', 'Operador de Puerta', 'Opera ingreso y salida desde dispositivos de acceso.', 'active'),
    ('44444444-4444-4444-4444-444444444406', 'student', 'Estudiante', 'Usuario institucional tipo estudiante.', 'active'),
    ('44444444-4444-4444-4444-444444444407', 'teacher', 'Docente', 'Usuario institucional tipo docente.', 'active'),
    ('44444444-4444-4444-4444-444444444408', 'employee', 'Empleado', 'Usuario institucional tipo trabajador.', 'active'),
    ('44444444-4444-4444-4444-444444444409', 'visitor', 'Visitante', 'Usuario temporal sin autorizacion permanente.', 'active'),
    ('44444444-4444-4444-4444-444444444410', 'auditor', 'Auditor', 'Consulta evidencias, reportes y auditoria.', 'active')
ON CONFLICT (role_key) DO UPDATE
SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    updated_at = NOW();
