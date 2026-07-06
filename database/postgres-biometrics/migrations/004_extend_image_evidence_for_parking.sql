ALTER TABLE image_evidence
    DROP CONSTRAINT IF EXISTS uq_image_evidence_sha256_hash;

ALTER TABLE image_evidence
    ADD COLUMN IF NOT EXISTS session_id UUID,
    ADD COLUMN IF NOT EXISTS plate VARCHAR(20),
    ADD COLUMN IF NOT EXISTS bucket VARCHAR(120),
    ADD COLUMN IF NOT EXISTS object_name TEXT,
    ADD COLUMN IF NOT EXISTS hash_sha256 CHAR(64);

UPDATE image_evidence
SET
    bucket = COALESCE(bucket, minio_bucket),
    object_name = COALESCE(object_name, object_path),
    hash_sha256 = COALESCE(hash_sha256, sha256_hash)
WHERE
    bucket IS NULL
    OR object_name IS NULL
    OR hash_sha256 IS NULL;

ALTER TABLE image_evidence
    ALTER COLUMN bucket SET NOT NULL,
    ALTER COLUMN object_name SET NOT NULL,
    ALTER COLUMN hash_sha256 SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_image_evidence_session_id ON image_evidence (session_id);
CREATE INDEX IF NOT EXISTS idx_image_evidence_plate ON image_evidence (plate);
