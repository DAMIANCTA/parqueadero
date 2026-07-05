from datetime import datetime

from pydantic import BaseModel, Field


class MinioImageReference(BaseModel):
    bucket: str
    object_path: str
    object_version: str | None = None
    sha256_hash: str | None = None
    content_type: str = "image/jpeg"
    image_type: str = "face_capture"


class FaceEnrollRequest(BaseModel):
    university_id: str
    person_id: str
    image_reference: MinioImageReference
    encrypted: bool = True
    expires_at: datetime | None = None
    quality_score_hint: float | None = Field(default=None, ge=0, le=1)


class FaceEnrollResponse(BaseModel):
    enrolled: bool
    template_id: str
    image_evidence_id: str
    university_id: str
    person_id: str
    model_name: str
    embedding_size: int
    quality_score: float = Field(ge=0, le=1)
    mode: str
    image_reference: MinioImageReference
    stored_in_biometric_db: bool = True


class FaceVerifyRequest(BaseModel):
    university_id: str
    person_id: str
    probe_image_reference: MinioImageReference
    template_id: str | None = None
    similarity_threshold: float | None = Field(default=None, ge=0, le=1)


class FaceVerifyResponse(BaseModel):
    match: bool
    score: float = Field(ge=0, le=1)
    threshold: float = Field(ge=0, le=1)
    template_id: str
    biometric_log_id: str
    model_name: str
    mode: str
    image_reference: MinioImageReference


class FaceCompareRequest(BaseModel):
    university_id: str | None = None
    source_image_reference: MinioImageReference
    target_image_reference: MinioImageReference
    similarity_threshold: float | None = Field(default=None, ge=0, le=1)


class FaceCompareResponse(BaseModel):
    match: bool
    score: float = Field(ge=0, le=1)
    threshold: float = Field(ge=0, le=1)
    biometric_log_id: str
    model_name: str
    mode: str
    source_image_reference: MinioImageReference
    target_image_reference: MinioImageReference


class FaceLivenessCheckRequest(BaseModel):
    university_id: str | None = None
    person_id: str | None = None
    image_reference: MinioImageReference
    challenge_type: str | None = None
    liveness_threshold: float | None = Field(default=None, ge=0, le=1)


class FaceLivenessCheckResponse(BaseModel):
    passed: bool
    score: float = Field(ge=0, le=1)
    threshold: float = Field(ge=0, le=1)
    biometric_log_id: str
    model_name: str
    mode: str
    image_reference: MinioImageReference
