from fastapi import APIRouter, HTTPException, Request, UploadFile
from minio.error import S3Error

from schemas.plates import PlateDetectRequest, PlateDetectResponse
from security import require_permissions
from services.image_source_service import ImageSourceService
from services.plate_detection_service import PlateDetectionService


router = APIRouter(tags=["plates"])
image_source_service = ImageSourceService()
plate_detection_service = PlateDetectionService()


@router.post("/plates/detect", response_model=PlateDetectResponse, dependencies=[require_permissions("plates.detect")])
async def detect_plate(request: Request) -> PlateDetectResponse:
    content_type = request.headers.get("content-type", "").lower()

    try:
        if content_type.startswith("application/json"):
            payload = PlateDetectRequest(**await request.json())
            loaded_image = image_source_service.load_from_minio(
                image_id=payload.plate_image_id or payload.image_id,
            )
            country_code = payload.country_code
        else:
            form = await request.form()
            image = form.get("image")
            image_id = _as_string(form.get("image_id")) or _as_string(form.get("plate_image_id"))
            bucket = _as_string(form.get("bucket"))
            object_name = _as_string(form.get("object_name"))
            country_code = _as_string(form.get("country_code"))

            using_upload = isinstance(image, UploadFile)
            using_reference = bool(image_id or (bucket and object_name))
            if using_upload and using_reference:
                raise HTTPException(status_code=400, detail="Use either upload image or image_id/bucket reference, not both")
            if not using_upload and not using_reference:
                raise HTTPException(status_code=400, detail="Provide an upload image or an image_id reference")

            if using_upload:
                if not image.filename:
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
                    image_id=image_id,
                    bucket=bucket,
                    object_name=object_name,
                )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except S3Error as exc:
        raise HTTPException(status_code=404, detail=f"MinIO object not found: {exc.code}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not loaded_image.content:
        raise HTTPException(status_code=400, detail="Image content is empty")

    return plate_detection_service.detect_plate(
        image_id=loaded_image.image_id,
        filename=loaded_image.filename,
        content_type=loaded_image.content_type,
        content=loaded_image.content,
        source=loaded_image.source,
        country_code=country_code,
        object_name=loaded_image.object_name,
    )


def _as_string(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
