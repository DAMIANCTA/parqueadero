from datetime import datetime

from pydantic import BaseModel, Field


class MinioImageReference(BaseModel):
    bucket: str
    object_path: str
    object_version: str | None = None
    sha256_hash: str | None = None
    content_type: str = "image/jpeg"
    image_type: str = "face_capture"


class FaceBoundingBoxResponse(BaseModel):
    x: int
    y: int
    width: int
    height: int


class FaceValidationSummary(BaseModel):
    detected: bool
    match: bool | None = None
    similarity: float | None = Field(default=None, ge=0, le=1)
    threshold: float | None = Field(default=None, ge=0, le=1)
    image_id: str | None = None
    session_id: str | None = None
    template_id: str | None = None
    bounding_box: FaceBoundingBoxResponse | None = None
    model_name: str
    provider: str
    mode: str
    quality_score: float | None = Field(default=None, ge=0, le=1)
    embedding_size: int = 0
    warnings: list[str] = Field(default_factory=list)


class FaceConfigResponse(BaseModel):
    environment: str
    face_service_mode: str
    face_real_provider: str
    similarity_threshold: float = Field(ge=0, le=1)
    liveness_threshold: float = Field(ge=0, le=1)
    embedding_dimensions: int
    opencv_available: bool
    insightface_available: bool
    face_recognition_available: bool = False
    provider_available: bool = False
    model_loaded: bool
    model_error: str | None = None
    active_provider: str


class FaceDetectRequest(BaseModel):
    image_id: str
    university_id: str
    person_id: str | None = None
    session_id: str | None = None
    quality_score_hint: float | None = Field(default=None, ge=0, le=1)


class FaceDetectResponse(FaceValidationSummary):
    detected_at: datetime
    stored_in_biometric_db: bool = True


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
    source_image_reference: MinioImageReference | None = None
    target_image_reference: MinioImageReference | None = None
    source_image_id: str | None = None
    target_image_id: str | None = None
    similarity_threshold: float | None = Field(default=None, ge=0, le=1)
    session_id: str | None = None
    gate_id: str | None = None


class FaceCompareResponse(FaceValidationSummary):
    biometric_log_id: str
    source_image_reference: MinioImageReference | None = None
    target_image_reference: MinioImageReference | None = None
    source_image_id: str | None = None
    target_image_id: str | None = None


class FaceVerifySessionRequest(BaseModel):
    university_id: str
    session_id: str
    probe_image_id: str
    similarity_threshold: float | None = Field(default=None, ge=0, le=1)
    gate_id: str | None = None


class FaceVerifySessionResponse(FaceValidationSummary):
    biometric_log_id: str
    probe_image_id: str


class FaceLivenessRequest(BaseModel):
    university_id: str
    image_id: str
    person_id: str | None = None
    session_id: str | None = None
    challenge_type: str | None = None
    liveness_threshold: float | None = Field(default=None, ge=0, le=1)


class FaceLivenessResponse(BaseModel):
    passed: bool
    score: float = Field(ge=0, le=1)
    threshold: float = Field(ge=0, le=1)
    biometric_log_id: str
    model_name: str
    mode: str
    image_id: str
    warnings: list[str] = Field(default_factory=list)


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
