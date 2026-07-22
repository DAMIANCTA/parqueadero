from typing import Literal

from pydantic import BaseModel, Field


PersonType = Literal["visitor", "student", "teacher", "employee", "driver"]
AccessType = Literal["VISITOR", "MEMBER"]


class ParkingEntryRequest(BaseModel):
    university_id: str
    campus_id: str
    gate_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    face_image_id: str
    plate_image_id: str | None = None
    face_mock_id: str | None = None
    face_evidence_id: str | None = None
    plate_evidence_id: str | None = None
    liveness_score: float = Field(ge=0, le=1)
    person_type: PersonType
    confidence_plate: float = Field(ge=0, le=1)
    confidence_face: float = Field(ge=0, le=1)
    operator_username: str | None = None
    plate_detected_text: str | None = None
    plate_detection_confidence: float | None = Field(default=None, ge=0, le=1)
    plate_override_reason: str | None = None


class ParkingExitRequest(BaseModel):
    university_id: str
    campus_id: str
    gate_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    face_image_id: str
    plate_image_id: str | None = None
    face_mock_id: str | None = None
    face_evidence_id: str | None = None
    plate_evidence_id: str | None = None
    liveness_score: float = Field(ge=0, le=1)
    confidence_plate: float = Field(ge=0, le=1)
    confidence_face: float = Field(ge=0, le=1)
    operator_username: str | None = None
    plate_detected_text: str | None = None
    plate_detection_confidence: float | None = Field(default=None, ge=0, le=1)
    plate_override_reason: str | None = None


class SessionData(BaseModel):
    session_id: str
    session_status: str
    payment_status: str
    person_type: PersonType
    plate_text: str
    access_type: AccessType
    person_id: str | None = None
    person_name: str | None = None
    role_type: str | None = None
    vehicle_id: str | None = None
    entry_time: str | None = None
    exit_time: str | None = None


class GateCommand(BaseModel):
    gate_id: str
    command: str
    published: bool


class FaceValidationResult(BaseModel):
    detected: bool
    match: bool | None = None
    similarity: float | None = Field(default=None, ge=0, le=1)
    threshold: float | None = Field(default=None, ge=0, le=1)
    image_id: str | None = None
    template_id: str | None = None
    provider: str
    model_name: str | None = None
    mode: str
    quality_score: float | None = Field(default=None, ge=0, le=1)
    embedding_size: int = 0
    bounding_box: dict | None = None
    warnings: list[str] = Field(default_factory=list)


class ParkingEntryResponse(BaseModel):
    authorized: bool
    status: Literal["AUTHORIZED", "REJECTED"]
    message: str
    session: SessionData | None = None
    gate_command: GateCommand | None = None
    face_validation: FaceValidationResult | None = None
    access_event_id: str
    audit_log_id: str
    incident_id: str | None = None


class ParkingExitResponse(BaseModel):
    authorized: bool
    status: Literal["AUTHORIZED", "REJECTED"]
    message: str
    session: SessionData | None = None
    gate_command: GateCommand | None = None
    face_validation: FaceValidationResult | None = None
    access_event_id: str
    audit_log_id: str
    incident_id: str | None = None


class ActiveSessionResponse(BaseModel):
    plate_text: str
    active: bool


class AccessHistoryItem(BaseModel):
    session_id: str
    session_status: str
    access_type: AccessType
    plate_text: str
    person_name: str | None = None
    payment_status: str
    entry_time: str | None = None
    exit_time: str | None = None
    entry_face_evidence_id: str | None = None
    entry_plate_evidence_id: str | None = None
    exit_face_evidence_id: str | None = None
    exit_plate_evidence_id: str | None = None


class ParkingHistoryResponse(BaseModel):
    total: int
    items: list[AccessHistoryItem]
