CREATE INDEX IF NOT EXISTS idx_campuses_university_id ON campuses (university_id);
CREATE INDEX IF NOT EXISTS idx_gates_university_id ON gates (university_id);
CREATE INDEX IF NOT EXISTS idx_gates_campus_id ON gates (campus_id);
CREATE INDEX IF NOT EXISTS idx_devices_university_id ON devices (university_id);
CREATE INDEX IF NOT EXISTS idx_devices_campus_id ON devices (campus_id);
CREATE INDEX IF NOT EXISTS idx_devices_gate_id ON devices (gate_id);
CREATE INDEX IF NOT EXISTS idx_users_university_id ON users (university_id);
CREATE INDEX IF NOT EXISTS idx_users_role_id ON users (role_id);
CREATE INDEX IF NOT EXISTS idx_persons_university_id ON persons (university_id);
CREATE INDEX IF NOT EXISTS idx_persons_campus_id ON persons (campus_id);
CREATE INDEX IF NOT EXISTS idx_persons_person_type ON persons (person_type);
CREATE INDEX IF NOT EXISTS idx_vehicles_university_id ON vehicles (university_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_authorizations_university_id ON vehicle_authorizations (university_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_authorizations_vehicle_id ON vehicle_authorizations (vehicle_id);
CREATE INDEX IF NOT EXISTS idx_vehicle_authorizations_person_id ON vehicle_authorizations (person_id);
CREATE INDEX IF NOT EXISTS idx_parking_sessions_university_id ON parking_sessions (university_id);
CREATE INDEX IF NOT EXISTS idx_parking_sessions_campus_id ON parking_sessions (campus_id);
CREATE INDEX IF NOT EXISTS idx_parking_sessions_vehicle_id ON parking_sessions (vehicle_id);
CREATE INDEX IF NOT EXISTS idx_parking_sessions_person_id ON parking_sessions (person_id);
CREATE INDEX IF NOT EXISTS idx_parking_sessions_status ON parking_sessions (session_status);
CREATE INDEX IF NOT EXISTS idx_parking_sessions_entry_time ON parking_sessions (entry_time);
CREATE INDEX IF NOT EXISTS idx_payments_university_id ON payments (university_id);
CREATE INDEX IF NOT EXISTS idx_payments_session_id ON payments (parking_session_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments (payment_status);
CREATE INDEX IF NOT EXISTS idx_access_events_university_id ON access_events (university_id);
CREATE INDEX IF NOT EXISTS idx_access_events_gate_id ON access_events (gate_id);
CREATE INDEX IF NOT EXISTS idx_access_events_session_id ON access_events (parking_session_id);
CREATE INDEX IF NOT EXISTS idx_access_events_occurred_at ON access_events (occurred_at);
CREATE INDEX IF NOT EXISTS idx_incidents_university_id ON incidents (university_id);
CREATE INDEX IF NOT EXISTS idx_incidents_gate_id ON incidents (gate_id);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents (incident_status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_university_id ON audit_logs (university_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_user_id ON audit_logs (actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs (created_at);

DROP TRIGGER IF EXISTS trg_universities_updated_at ON universities;
CREATE TRIGGER trg_universities_updated_at
BEFORE UPDATE ON universities
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_campuses_updated_at ON campuses;
CREATE TRIGGER trg_campuses_updated_at
BEFORE UPDATE ON campuses
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_gates_updated_at ON gates;
CREATE TRIGGER trg_gates_updated_at
BEFORE UPDATE ON gates
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_devices_updated_at ON devices;
CREATE TRIGGER trg_devices_updated_at
BEFORE UPDATE ON devices
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_roles_updated_at ON roles;
CREATE TRIGGER trg_roles_updated_at
BEFORE UPDATE ON roles
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_persons_updated_at ON persons;
CREATE TRIGGER trg_persons_updated_at
BEFORE UPDATE ON persons
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_vehicles_updated_at ON vehicles;
CREATE TRIGGER trg_vehicles_updated_at
BEFORE UPDATE ON vehicles
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_vehicle_authorizations_updated_at ON vehicle_authorizations;
CREATE TRIGGER trg_vehicle_authorizations_updated_at
BEFORE UPDATE ON vehicle_authorizations
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_parking_sessions_updated_at ON parking_sessions;
CREATE TRIGGER trg_parking_sessions_updated_at
BEFORE UPDATE ON parking_sessions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_payments_updated_at ON payments;
CREATE TRIGGER trg_payments_updated_at
BEFORE UPDATE ON payments
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_access_events_updated_at ON access_events;
CREATE TRIGGER trg_access_events_updated_at
BEFORE UPDATE ON access_events
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_incidents_updated_at ON incidents;
CREATE TRIGGER trg_incidents_updated_at
BEFORE UPDATE ON incidents
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_audit_logs_updated_at ON audit_logs;
CREATE TRIGGER trg_audit_logs_updated_at
BEFORE UPDATE ON audit_logs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
