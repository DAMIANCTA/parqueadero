from pydantic import BaseModel, Field


class GateOpenRequest(BaseModel):
    university_id: str
    campus_id: str
    gate_id: str
    plate: str = Field(min_length=3, max_length=20)
    session_id: str | None = None
    reason: str = Field(min_length=3, max_length=120)
    command: str = "open"


class GateOpenResponse(BaseModel):
    gate_id: str
    command: str
    published: bool
    topic: str
    status_topic: str
    payload: dict


class GateStatusRequest(BaseModel):
    university_id: str
    campus_id: str
    gate_id: str
    plate: str = Field(min_length=3, max_length=20)
    barrier: str = "closed"
    device_status: str = "online"
    reason: str = Field(min_length=3, max_length=120)
    event_type: str = Field(min_length=3, max_length=40)
    access_status: str = Field(min_length=3, max_length=40)


class GateStatusResponse(BaseModel):
    gate_id: str
    published: bool
    topic: str
    payload: dict
