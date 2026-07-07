from typing import Literal

from pydantic import BaseModel, Field


PlateDetectionStatus = Literal["DETECTED", "LOW_CONFIDENCE", "NOT_DETECTED"]


class PlateDetectRequest(BaseModel):
    image_id: str = Field(min_length=1)
    university_id: str | None = None
    campus_id: str | None = None
    gate_id: str | None = None
    country_code: str | None = None
    plate_image_id: str | None = None


class BoundingBox(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class PlateCandidateResponse(BaseModel):
    text: str
    confidence: float = Field(ge=0, le=1)


class PlateDetectResponse(BaseModel):
    image_id: str
    plate_text: str | None = None
    confidence: float = Field(ge=0, le=1)
    bounding_box: BoundingBox | None = None
    candidates: list[PlateCandidateResponse] = Field(default_factory=list)
    status: PlateDetectionStatus
    mode: str
    valid_format: bool
    source: str
    detector_provider: str
    ocr_provider: str
    warnings: list[str] = Field(default_factory=list)
