from typing import Literal

from pydantic import BaseModel, Field


PersonType = Literal["visitor", "student", "teacher", "employee"]


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
    person_type: str | None = None
    plate_text: str


class GateCommand(BaseModel):
    gate_id: str
    command: str
    published: bool
    topic: str | None = None
    status_topic: str | None = None
    payload: dict | None = None


class ParkingAuthorizationResponse(BaseModel):
    authorized: bool
    status: str
    message: str
    session: SessionData | None = None
    gate_command: GateCommand | None = None
    access_event_id: str
    audit_log_id: str
    incident_id: str | None = None


class DemoOpenGateRequest(BaseModel):
    university_id: str = Field(min_length=1)
    campus_id: str = Field(min_length=1)
    gate_id: str = Field(min_length=1)
    plate: str = Field(min_length=3, max_length=20)


class DemoOpenGateResponse(BaseModel):
    status: Literal["OPEN_COMMAND_SENT"]
    message: str
    demo_event_id: str
    topic: str
    status_topic: str
    command: str
    published: bool
    payload: dict


class PaymentByPlateRequest(BaseModel):
    plate_text: str = Field(min_length=3, max_length=20)
    cashier_user_id: str = "cashier-demo"
    payment_method: str = "cash"


class PaymentByPlateResponse(BaseModel):
    success: bool
    message: str
    session: dict | None = None
    audit_log_id: str


class EvidenceUploadResponse(BaseModel):
    image_id: str
    bucket: str
    object_name: str
    image_type: str
    session_id: str | None = None
    plate: str
    hash_sha256: str
    encrypted: bool
    created_at: str
    expires_at: str | None = None
    status: str


class PlateDetectRequest(BaseModel):
    image_id: str = Field(min_length=1)
    university_id: str | None = None
    campus_id: str | None = None
    gate_id: str | None = None
    country_code: str | None = None
    plate_image_id: str | None = None


class PlateCandidateResponse(BaseModel):
    text: str
    confidence: float = Field(ge=0, le=1)


class PlateDetectResponse(BaseModel):
    image_id: str
    plate_text: str
    confidence: float = Field(ge=0, le=1)
    bounding_box: dict
    candidates: list[PlateCandidateResponse]
    status: str
    mode: str
    valid_format: bool
    source: str
    detector_provider: str
    ocr_provider: str
