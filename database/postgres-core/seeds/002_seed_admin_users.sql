INSERT INTO users (
    id,
    university_id,
    role_id,
    username,
    email,
    password_hash,
    first_name,
    last_name,
    status
)
VALUES
    (
        '55555555-5555-5555-5555-555555555501',
        NULL,
        '44444444-4444-4444-4444-444444444401',
        'super.admin',
        'super.admin@smartparking.local',
        '684181f5dc7c6785319c24bf8fe4f0c5932fd9d7e87c95760c39280623d432fc',
        'Super',
        'Administrador',
        'active'
    ),
    (
        '55555555-5555-5555-5555-555555555502',
        '11111111-1111-1111-1111-111111111111',
        '44444444-4444-4444-4444-444444444402',
        'admin.university',
        'admin.university@uce.edu.ec',
        'e5580937920ec3f7c0c726f6fdf29b8c9914072a508d1a73e2e4a50ce8912e75',
        'Administrador',
        'Universidad',
        'active'
    ),
    (
        '55555555-5555-5555-5555-555555555503',
        '11111111-1111-1111-1111-111111111111',
        '44444444-4444-4444-4444-444444444404',
        'cashier.uce',
        'cashier@uce.edu.ec',
        'a0ea9f17f048df0b0a4167944a8a82ebe1da01a0f025e083bece9eaf84f60219',
        'Caja',
        'UCE',
        'active'
    ),
    (
        '55555555-5555-5555-5555-555555555504',
        '11111111-1111-1111-1111-111111111111',
        '44444444-4444-4444-4444-444444444405',
        'members.uce',
        'members@uce.edu.ec',
        '6f45f1d82e5ac63fadf9f139cd1395070643bf01bd3198708d0163c19b8144f8',
        'Miembros',
        'UCE',
        'active'
    ),
    (
        '55555555-5555-5555-5555-555555555505',
        '11111111-1111-1111-1111-111111111111',
        '44444444-4444-4444-4444-444444444403',
        'security.uce',
        'security@uce.edu.ec',
        '2d0e8b14224c1042dc20799026b11ab338ecdf00508241c5ff67a8dab15b8337',
        'Seguridad',
        'UCE',
        'active'
    ),
    (
        '55555555-5555-5555-5555-555555555506',
        '11111111-1111-1111-1111-111111111111',
        '44444444-4444-4444-4444-444444444411',
        'auditor.uce',
        'auditor@uce.edu.ec',
        'ed8dccfc66ddf141cc34aaf52213424eeec22f69a1ba928b92666bc886e2fdaf',
        'Auditor',
        'UCE',
        'active'
    )
ON CONFLICT (username) DO UPDATE
SET
    university_id = EXCLUDED.university_id,
    role_id = EXCLUDED.role_id,
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    status = EXCLUDED.status,
    updated_at = NOW();
