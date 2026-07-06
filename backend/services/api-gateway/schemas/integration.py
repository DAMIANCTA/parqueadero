from typing import Literal

from pydantic import BaseModel, Field


PersonType = Literal["visitor", "student", "teacher", "employee"]


class ParkingEntryRequest(BaseModel):
    university_id: str
    campus_id: str
    gate_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    face_image_id: str
    liveness_score: float = Field(ge=0, le=1)
    person_type: PersonType
    confidence_plate: float = Field(ge=0, le=1)
    confidence_face: float = Field(ge=0, le=1)


class ParkingExitRequest(BaseModel):
    university_id: str
    campus_id: str
    gate_id: str
    plate_text: str = Field(min_length=3, max_length=20)
    face_image_id: str
    liveness_score: float = Field(ge=0, le=1)
    confidence_plate: float = Field(ge=0, le=1)
    confidence_face: float = Field(ge=0, le=1)


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
