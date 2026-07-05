from typing import Any

from pydantic import BaseModel


class AuditEventRequest(BaseModel):
    service: str
    timestamp: int
    method: str
    path: str
    status_code: int
    duration_ms: float
    client_ip: str
    actor_user_id: str | None = None
    actor_username: str | None = None
    actor_roles: list[str] = []


class AuditEventResponse(BaseModel):
    accepted: bool
    event_id: str


class AuditLogListResponse(BaseModel):
    total: int
    items: list[dict[str, Any]]
