CREATE TABLE IF NOT EXISTS image_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL,
    person_id UUID,
    minio_bucket VARCHAR(120) NOT NULL,
    object_path TEXT NOT NULL,
    object_version VARCHAR(120),
    sha256_hash CHAR(64) NOT NULL,
    image_type VARCHAR(30) NOT NULL
        CHECK (image_type IN (
            'face_entry',
            'face_exit',
            'face_enrollment',
            'plate_entry',
            'plate_exit',
            'liveness_frame',
            'incident_capture',
            'other'
        )),
    content_type VARCHAR(80) DEFAULT 'image/jpeg',
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    encrypted BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'expired', 'deleted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_image_evidence_sha256_hash UNIQUE (sha256_hash),
    CONSTRAINT uq_image_evidence_object UNIQUE (minio_bucket, object_path)
);

CREATE TABLE IF NOT EXISTS face_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL,
    person_id UUID NOT NULL,
    source_image_evidence_id UUID REFERENCES image_evidence(id) ON DELETE SET NULL,
    embedding_vector VECTOR(512),
    model_name VARCHAR(120) NOT NULL,
    quality_score NUMERIC(5, 4) CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)),
    encrypted BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'expired', 'revoked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS biometric_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID NOT NULL,
    person_id UUID,
    face_template_id UUID REFERENCES face_templates(id) ON DELETE SET NULL,
    image_evidence_id UUID REFERENCES image_evidence(id) ON DELETE SET NULL,
    session_reference_id UUID,
    gate_reference_id UUID,
    device_reference_id UUID,
    operation_type VARCHAR(30) NOT NULL
        CHECK (operation_type IN ('enrollment', 'entry_validation', 'exit_validation', 'revalidation', 'manual_review')),
    model_name VARCHAR(120) NOT NULL,
    similarity_score NUMERIC(5, 4) CHECK (similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1)),
    quality_score NUMERIC(5, 4) CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)),
    liveness_score NUMERIC(5, 4) CHECK (liveness_score IS NULL OR (liveness_score >= 0 AND liveness_score <= 1)),
    decision VARCHAR(20) NOT NULL
        CHECK (decision IN ('approved', 'rejected', 'manual_review', 'error')),
    encrypted BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive', 'expired')),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
