CREATE INDEX IF NOT EXISTS idx_image_evidence_university_id ON image_evidence (university_id);
CREATE INDEX IF NOT EXISTS idx_image_evidence_person_id ON image_evidence (person_id);
CREATE INDEX IF NOT EXISTS idx_image_evidence_image_type ON image_evidence (image_type);
CREATE INDEX IF NOT EXISTS idx_image_evidence_expires_at ON image_evidence (expires_at);
CREATE INDEX IF NOT EXISTS idx_face_templates_university_id ON face_templates (university_id);
CREATE INDEX IF NOT EXISTS idx_face_templates_person_id ON face_templates (person_id);
CREATE INDEX IF NOT EXISTS idx_face_templates_model_name ON face_templates (model_name);
CREATE INDEX IF NOT EXISTS idx_face_templates_status ON face_templates (status);
CREATE INDEX IF NOT EXISTS idx_biometric_access_logs_university_id ON biometric_access_logs (university_id);
CREATE INDEX IF NOT EXISTS idx_biometric_access_logs_person_id ON biometric_access_logs (person_id);
CREATE INDEX IF NOT EXISTS idx_biometric_access_logs_template_id ON biometric_access_logs (face_template_id);
CREATE INDEX IF NOT EXISTS idx_biometric_access_logs_image_id ON biometric_access_logs (image_evidence_id);
CREATE INDEX IF NOT EXISTS idx_biometric_access_logs_occurred_at ON biometric_access_logs (occurred_at);
CREATE INDEX IF NOT EXISTS idx_biometric_access_logs_operation_type ON biometric_access_logs (operation_type);

DROP TRIGGER IF EXISTS trg_image_evidence_updated_at ON image_evidence;
CREATE TRIGGER trg_image_evidence_updated_at
BEFORE UPDATE ON image_evidence
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_face_templates_updated_at ON face_templates;
CREATE TRIGGER trg_face_templates_updated_at
BEFORE UPDATE ON face_templates
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_biometric_access_logs_updated_at ON biometric_access_logs;
CREATE TRIGGER trg_biometric_access_logs_updated_at
BEFORE UPDATE ON biometric_access_logs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
