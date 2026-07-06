from typing import Any

from pydantic import BaseModel


class DependencyHealth(BaseModel):
    name: str
    status: str
    detail: str


class HealthResponse(BaseModel):
    service: str
    status: str
    version: str
    environment: str
    checks: list[DependencyHealth] = []


class VersionResponse(BaseModel):
    service: str
    version: str


class MockResponse(BaseModel):
    service: str
    resource: str
    data: dict[str, Any]
