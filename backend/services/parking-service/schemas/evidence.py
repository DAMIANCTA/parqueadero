from typing import Literal

from pydantic import BaseModel, Field


ImageType = Literal["face_entry", "face_exit", "plate_entry", "plate_exit", "incident_capture"]


class EvidenceUploadResponse(BaseModel):
    image_id: str
    bucket: str
    object_name: str
    image_type: ImageType
    session_id: str | None = None
    plate: str = Field(min_length=3, max_length=20)
    hash_sha256: str
    encrypted: bool
    created_at: str
    expires_at: str | None = None
    status: str


class TemporaryUserRecord(BaseModel):
    id: str
    university_id: str
    plate: str
    full_name: str | None = None
    face_template_id: str | None = None
    entry_face_evidence_id: str | None = None
    entry_plate_evidence_id: str | None = None
    entry_session_id: str | None = None
    entry_gate_id: str | None = None
    face_model_name: str | None = None
    liveness_score: float | None = None
    metadata: dict
    status: str
    created_at: str
    expires_at: str


class EvidenceByPlateResponse(BaseModel):
    plate_text: str
    count: int
    temporary_users: list[TemporaryUserRecord]
