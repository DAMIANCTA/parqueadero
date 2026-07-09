from typing import Literal
from datetime import date, datetime

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
    access_type: str | None = None
    person_id: str | None = None
    person_name: str | None = None
    role_type: str | None = None
    vehicle_id: str | None = None
    permit_status: str | None = None
    entry_time: str | None = None
    exit_time: str | None = None


class GateCommand(BaseModel):
    gate_id: str
    command: str
    published: bool
    topic: str | None = None
    status_topic: str | None = None
    payload: dict | None = None


class FaceValidationResponse(BaseModel):
    detected: bool
    match: bool | None = None
    similarity: float | None = Field(default=None, ge=0, le=1)
    distance: float | None = None
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


class ParkingAuthorizationResponse(BaseModel):
    authorized: bool
    status: str
    message: str
    session: SessionData | None = None
    gate_command: GateCommand | None = None
    face_validation: FaceValidationResponse | None = None
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


class CashierPaymentLookupResponse(BaseModel):
    found: bool
    message: str
    session_id: str | None = None
    plate_text: str | None = None
    entry_time: str | None = None
    exit_time: str | None = None
    session_status: str | None = None
    duration_minutes: int | None = None
    amount: float | None = None
    currency: str | None = None
    payment_status: str | None = None
    paid_at: str | None = None
    paid_amount: float | None = None
    payment_method: str | None = None
    payment_valid_until: str | None = None
    receipt_number: str | None = None
    access_type: str | None = None
    person_id: str | None = None
    person_name: str | None = None
    role_type: str | None = None
    permit_status: str | None = None


class IotGateCommandRequest(BaseModel):
    university_id: str | None = None
    campus_id: str | None = None
    plate: str | None = Field(default=None, min_length=3, max_length=20)
    session_id: str | None = None
    reason: str = Field(min_length=3, max_length=120)


class IotGateCommandResponse(BaseModel):
    gate_id: str
    status: str
    command: str
    command_code: str
    published: bool
    topic: str
    mqtt_connected: bool
    payload: str
    event_topic: str
    timestamp: str
    reason: str


class IotGateStatusResponse(BaseModel):
    gate_id: str
    status: str
    mqtt_connected: bool
    command_topic: str
    event_topic: str
    last_event_type: str | None = None
    last_event_payload: str | None = None
    last_presence_at: str | None = None
    last_command: str | None = None
    last_command_at: str | None = None
    last_updated_at: str | None = None
    last_reason: str | None = None
    university_id: str | None = None
    campus_id: str | None = None
    plate: str | None = None
    session_id: str | None = None


class CashierPaymentRegistrationRequest(BaseModel):
    session_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    amount: float = Field(gt=0)
    payment_method: str
    cashier_user_id: str = Field(min_length=3, max_length=100)
    notes: str | None = None


class CashierPaymentRegistrationResponse(BaseModel):
    success: bool
    message: str
    receipt_number: str | None = None
    paid_at: str | None = None
    audit_log_id: str
    session: CashierPaymentLookupResponse | None = None


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


class PlateDetectBatchRequest(BaseModel):
    image_ids: list[str] = Field(min_length=1, max_length=10)
    university_id: str | None = None
    campus_id: str | None = None
    gate_id: str | None = None
    country_code: str | None = None


class PlateCandidateResponse(BaseModel):
    text: str
    confidence: float = Field(ge=0, le=1)


class PlateDetectResponse(BaseModel):
    image_id: str
    plate_text: str | None = None
    confidence: float = Field(ge=0, le=1)
    bounding_box: dict | None = None
    candidates: list[PlateCandidateResponse] = Field(default_factory=list)
    status: str
    mode: str
    valid_format: bool
    source: str
    detector_provider: str
    ocr_provider: str
    warnings: list[str] = Field(default_factory=list)


class PlateBatchResultItem(BaseModel):
    image_id: str
    plate_text: str | None = None
    confidence: float = Field(ge=0, le=1)
    status: str


class PlateDetectBatchResponse(BaseModel):
    status: str
    plate_text: str | None = None
    confidence: float = Field(ge=0, le=1)
    results: list[PlateBatchResultItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FaceServiceConfigResponse(BaseModel):
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


class MemberCreateRequest(BaseModel):
    university_id: str
    document_id: str
    institutional_id: str
    full_name: str
    email: str
    role_type: Literal["STUDENT", "TEACHER", "STAFF"]
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"


class MemberResponse(BaseModel):
    id: str
    university_id: str
    document_id: str
    institutional_id: str
    full_name: str
    email: str
    role_type: str
    status: str
    created_at: datetime
    updated_at: datetime


class MemberListResponse(BaseModel):
    total: int
    items: list[MemberResponse]


class VehicleCreateRequest(BaseModel):
    university_id: str
    plate_text: str
    brand: str
    model: str
    color: str
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"


class VehicleResponse(BaseModel):
    id: str
    university_id: str
    plate_text: str
    brand: str
    model: str
    color: str
    status: str
    created_at: datetime
    updated_at: datetime


class VehicleListResponse(BaseModel):
    total: int
    items: list[VehicleResponse]


class VehicleAuthorizationRequest(BaseModel):
    person_id: str
    is_owner: bool = False
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"


class VehicleAuthorizationResponse(BaseModel):
    id: str
    university_id: str
    person_id: str
    vehicle_id: str
    is_owner: bool
    status: str
    created_at: datetime
    updated_at: datetime


class VehicleLookupResponse(BaseModel):
    found: bool
    message: str
    vehicle: VehicleResponse | None = None
    authorized_people: list[MemberResponse] = Field(default_factory=list)


class FaceEnrollMemberRequest(BaseModel):
    face_image_id: str
    quality_score_hint: float | None = Field(default=None, ge=0, le=1)
    provider_hint: str | None = None


class FaceProfileResponse(BaseModel):
    id: str
    university_id: str
    person_id: str
    face_image_id: str
    template_id: str
    embedding_id: str
    provider: str
    status: str
    created_at: datetime
    updated_at: datetime


class FaceProfileListResponse(BaseModel):
    total: int
    items: list[FaceProfileResponse]


class MonthlyPermitCreateRequest(BaseModel):
    university_id: str
    person_id: str
    vehicle_id: str
    start_date: date
    end_date: date
    amount: float
    payment_method: str
    status: Literal["VALID", "EXPIRED", "SUSPENDED"] = "VALID"
    paid_at: datetime | None = None
    receipt_number: str | None = None


class MonthlyPermitResponse(BaseModel):
    id: str
    university_id: str
    person_id: str
    vehicle_id: str
    start_date: date
    end_date: date
    amount: float
    payment_method: str
    status: str
    paid_at: datetime | None = None
    receipt_number: str | None = None
    created_at: datetime
    updated_at: datetime


class MonthlyPermitListResponse(BaseModel):
    total: int
    items: list[MonthlyPermitResponse]


class PermitLookupResponse(BaseModel):
    found: bool
    plate_text: str | None = None
    permit_status: str | None = None
    person_id: str | None = None
    person_name: str | None = None
    role_type: str | None = None
    vehicle_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    message: str


class MemberAccessValidationRequest(BaseModel):
    university_id: str
    plate_text: str
    face_image_id: str
    gate_id: str
    session_person_id: str | None = None


class MemberAccessValidationResponse(BaseModel):
    authorized: bool
    access_type: str = "MEMBER"
    vehicle_registered: bool = False
    person_id: str | None = None
    person_name: str | None = None
    role_type: str | None = None
    vehicle_id: str | None = None
    plate_text: str
    permit_status: str | None = None
    face_match: bool = False
    similarity: float = Field(default=0, ge=0, le=1)
    template_id: str | None = None
    provider: str | None = None
    message: str
    warnings: list[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=100)


class GatewayTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    roles: list[str]
    permissions: list[str]
    university_id: str | None = None


class CurrentUserResponse(BaseModel):
    sub: str
    username: str
    roles: list[str]
    permissions: list[str]
    university_id: str | None = None


class AdminDashboardSummaryResponse(BaseModel):
    active_sessions: int
    vehicles_inside: int
    pending_payments: int
    paid_today: int
    revenue_today: float
    authorized_exits_today: int
    rejected_exits_today: int


class AdminSessionItemResponse(BaseModel):
    session_id: str
    plate_text: str
    entry_time: str
    exit_time: str | None = None
    duration_minutes: int
    amount: float
    currency: str
    payment_status: str
    session_status: str
    payment_method: str | None = None
    paid_at: str | None = None
    paid_amount: float | None = None
    payment_valid_until: str | None = None
    receipt_number: str | None = None


class AdminSessionListResponse(BaseModel):
    total: int
    items: list[AdminSessionItemResponse]


class AdminAuditEventItemResponse(BaseModel):
    id: str | None = None
    timestamp: int | None = None
    service: str | None = None
    method: str | None = None
    path: str | None = None
    status_code: int | None = None
    duration_ms: float | None = None
    client_ip: str | None = None
    actor_user_id: str | None = None
    actor_username: str | None = None
    actor_roles: list[str] = Field(default_factory=list)


class AdminAuditEventListResponse(BaseModel):
    total: int
    items: list[AdminAuditEventItemResponse]
