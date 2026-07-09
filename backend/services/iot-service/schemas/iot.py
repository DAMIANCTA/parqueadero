from pydantic import BaseModel, Field


class GateActionRequest(BaseModel):
    university_id: str | None = None
    campus_id: str | None = None
    plate: str | None = Field(default=None, min_length=3, max_length=20)
    session_id: str | None = None
    reason: str = Field(min_length=3, max_length=120)


class GateCommandResponse(BaseModel):
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


class GateRuntimeStatusResponse(BaseModel):
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


class LegacyGateOpenRequest(BaseModel):
    university_id: str
    campus_id: str
    gate_id: str
    plate: str = Field(min_length=3, max_length=20)
    session_id: str | None = None
    reason: str = Field(min_length=3, max_length=120)
    command: str = "open"


class LegacyGateOpenResponse(BaseModel):
    gate_id: str
    command: str
    published: bool
    topic: str
    status_topic: str
    payload: dict


class LegacyGateStatusRequest(BaseModel):
    university_id: str
    campus_id: str
    gate_id: str
    plate: str = Field(min_length=3, max_length=20)
    barrier: str = "closed"
    device_status: str = "online"
    reason: str = Field(min_length=3, max_length=120)
    event_type: str = Field(min_length=3, max_length=40)
    access_status: str = Field(min_length=3, max_length=40)


class LegacyGateStatusResponse(BaseModel):
    gate_id: str
    published: bool
    topic: str
    payload: dict
