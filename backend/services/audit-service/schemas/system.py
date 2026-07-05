from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    status: str
    version: str
    environment: str


class VersionResponse(BaseModel):
    service: str
    version: str


class MockResponse(BaseModel):
    service: str
    resource: str
    data: dict[str, Any]
