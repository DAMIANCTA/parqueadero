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


class PlateConfigResponse(BaseModel):
    environment: str
    plate_service_mode: str
    plate_detection_mode: str
    opencv_available: bool
    easyocr_available: bool
    rapidocr_available: bool
    paddleocr_available: bool
    ocr_engine: str
    model_path: str
    model_exists: bool
    min_confidence: float
