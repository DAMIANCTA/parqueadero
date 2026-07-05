from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from config import settings
from schemas.plates import PlateDetectResponse
from services.plate_detection_service import PlateDetectionService


router = APIRouter(tags=["plates"])


@router.post("/plates/detect", response_model=PlateDetectResponse)
async def detect_plate(
    image: UploadFile = File(...),
    country_code: str | None = Form(default=None),
) -> PlateDetectResponse:
    if not image.filename:
        raise HTTPException(status_code=400, detail="Image filename is required")

    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="Image content is empty")

    service = PlateDetectionService()
    response = service.detect_plate(
        filename=image.filename,
        content_type=image.content_type or "application/octet-stream",
        content=content,
        country_code=country_code or settings.plate_default_country_code,
    )
    if response.confidence < settings.plate_min_confidence and response.mode == "real":
        raise HTTPException(status_code=422, detail="Plate detection confidence below threshold")
    return response
