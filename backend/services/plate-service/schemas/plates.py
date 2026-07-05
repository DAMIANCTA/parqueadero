from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class PlateDetectResponse(BaseModel):
    plate_text: str
    confidence: float = Field(ge=0, le=1)
    bounding_box: BoundingBox
    mode: str
    valid_format: bool
