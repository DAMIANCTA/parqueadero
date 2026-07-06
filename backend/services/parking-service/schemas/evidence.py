from typing import Literal

from pydantic import BaseModel, Field


ImageType = Literal["face_entry", "face_exit", "plate_entry", "plate_exit"]


class EvidenceUploadResponse(BaseModel):
    image_id: str
    bucket: str
    object_name: str
    image_type: ImageType
    session_id: str | None = None
    plate: str = Field(min_length=3, max_length=20)
    created_at: str
