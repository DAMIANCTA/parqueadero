from fastapi import APIRouter, HTTPException, Request
from minio.error import S3Error
from psycopg import OperationalError
from starlette.datastructures import UploadFile

from config import settings
from schemas.plates import (
    PlateCandidateResponse,
    PlateDetectBatchRequest,
    PlateDetectBatchResponse,
    PlateDetectRequest,
    PlateDetectResponse,
)
from security import require_permissions
from services.plate_service import PlateService


router = APIRouter(tags=["plates"])
plate_service = PlateService()


@router.post("/plates/detect", response_model=PlateDetectResponse, dependencies=[require_permissions("plates.detect")])
async def detect_plate(request: Request) -> PlateDetectResponse:
    content_type = request.headers.get("content-type", "").lower()
    response_source = "minio"

    try:
        if content_type.startswith("application/json"):
            payload = PlateDetectRequest(**await request.json())
            outcome = plate_service.detect_plate(
                image_id=payload.plate_image_id or payload.image_id,
                country_code=payload.country_code,
            )
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
                response_source = "upload"
                if not image.filename:
                    raise HTTPException(status_code=400, detail="Image filename is required")
                content = await image.read()
                if not content:
                    raise HTTPException(status_code=400, detail="Image content is empty")
                outcome = plate_service.detect_plate(
                    image_id=image_id,
                    upload_bytes=content,
                    upload_filename=image.filename,
                    upload_content_type=image.content_type or "application/octet-stream",
                    country_code=country_code,
                )
            else:
                outcome = plate_service.detect_plate(
                    image_id=image_id,
                    bucket=bucket,
                    object_name=object_name,
                    country_code=country_code,
                )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except S3Error as exc:
        raise HTTPException(status_code=404, detail=f"MinIO object not found: {exc.code}") from exc
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="BIOMETRIC_DB_UNAVAILABLE") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PlateDetectResponse(
        image_id=outcome.image_id,
        plate_text=outcome.plate_text,
        confidence=outcome.confidence,
        bounding_box=outcome.bounding_box,
        candidates=[
            PlateCandidateResponse(text=candidate.text, confidence=candidate.confidence)
            for candidate in outcome.candidates
        ],
        status=outcome.status,
        mode=settings.effective_plate_detection_mode,
        valid_format=outcome.valid_format,
        source=response_source,
        detector_provider=outcome.detector_provider,
        ocr_provider=outcome.ocr_provider,
        warnings=outcome.warnings,
    )


@router.post("/plates/detect-batch", response_model=PlateDetectBatchResponse, dependencies=[require_permissions("plates.detect")])
async def detect_plate_batch(payload: PlateDetectBatchRequest) -> PlateDetectBatchResponse:
    try:
        outcome = plate_service.detect_plate_batch(
            image_ids=payload.image_ids,
            country_code=payload.country_code,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except S3Error as exc:
        raise HTTPException(status_code=404, detail=f"MinIO object not found: {exc.code}") from exc
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="BIOMETRIC_DB_UNAVAILABLE") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PlateDetectBatchResponse(
        status=outcome.status,
        plate_text=outcome.plate_text,
        confidence=outcome.confidence,
        results=[
            {
                "image_id": result.image_id,
                "plate_text": result.plate_text,
                "confidence": result.confidence,
                "status": result.status,
            }
            for result in outcome.results
        ],
        warnings=outcome.warnings,
    )


def _as_string(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
