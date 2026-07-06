from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from minio.error import S3Error

from config import settings
from schemas.plates import PlateDetectResponse
from security import require_permissions
from services.image_source_service import ImageSourceService
from services.plate_detection_service import PlateDetectionService


router = APIRouter(tags=["plates"])
image_source_service = ImageSourceService()
plate_detection_service = PlateDetectionService()


@router.post("/plates/detect", response_model=PlateDetectResponse, dependencies=[require_permissions("plates.detect")])
async def detect_plate(
    image: UploadFile | None = File(default=None),
    image_id: str | None = Form(default=None),
    bucket: str | None = Form(default=None),
    object_name: str | None = Form(default=None),
    country_code: str | None = Form(default=None),
) -> PlateDetectResponse:
    using_upload = image is not None
    using_minio = bool(bucket and object_name)

    if using_upload and using_minio:
        raise HTTPException(status_code=400, detail="Use either upload image or bucket/object_name, not both")
    if not using_upload and not using_minio:
        raise HTTPException(status_code=400, detail="Provide an upload image or a MinIO reference")

    try:
        if using_upload:
            if not image or not image.filename:
                raise HTTPException(status_code=400, detail="Image filename is required")
            content = await image.read()
            if not content:
                raise HTTPException(status_code=400, detail="Image content is empty")
            loaded_image = image_source_service.load_from_upload(
                filename=image.filename,
                content_type=image.content_type or "application/octet-stream",
                content=content,
                image_id=image_id,
            )
        else:
            loaded_image = image_source_service.load_from_minio(
                bucket=bucket or "",
                object_name=object_name or "",
                image_id=image_id,
            )
    except S3Error as exc:
        raise HTTPException(status_code=404, detail=f"MinIO object not found: {exc.code}") from exc

    if not loaded_image.content:
        raise HTTPException(status_code=400, detail="Image content is empty")

    response = plate_detection_service.detect_plate(
        image_id=loaded_image.image_id,
        filename=loaded_image.filename,
        content_type=loaded_image.content_type,
        content=loaded_image.content,
        source=loaded_image.source,
        country_code=country_code or settings.plate_default_country_code,
    )
    if response.confidence < settings.plate_min_confidence and response.mode == "real":
        raise HTTPException(status_code=422, detail="Plate detection confidence below threshold")
    return response
