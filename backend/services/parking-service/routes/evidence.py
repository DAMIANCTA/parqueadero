from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from repositories.temporary_user_repository import TemporaryUserRepository
from schemas.evidence import EvidenceByPlateResponse, EvidenceUploadResponse, ImageType
from services.evidence_storage_service import EvidenceStorageService


router = APIRouter(prefix="/evidence", tags=["evidence"])
evidence_service = EvidenceStorageService()
temporary_user_repository = TemporaryUserRepository()


@router.post("/upload", response_model=EvidenceUploadResponse)
async def upload_evidence(
    image_type: ImageType = Form(...),
    plate: str = Form(...),
    university_id: str | None = Form(default=None),
    session_id: str | None = Form(default=None),
    file: UploadFile = File(...),
) -> EvidenceUploadResponse:
    payload = await file.read()
    try:
        evidence = evidence_service.upload_evidence(
            file_bytes=payload,
            filename=file.filename or "evidence.bin",
            content_type=file.content_type or "application/octet-stream",
            image_type=image_type,
            plate=plate,
            university_id=university_id,
            session_id=session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Evidence upload failed: {exc}") from exc
    return EvidenceUploadResponse(**evidence)


@router.get("/image/{image_id}")
def get_evidence_image(image_id: str) -> Response:
    result = evidence_service.get_image_bytes(image_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Evidence image not found")
    payload, content_type = result
    return Response(content=payload, media_type=content_type)


@router.get("/by-plate/{plate_text}", response_model=EvidenceByPlateResponse)
def get_evidence_by_plate(plate_text: str, include_expired: bool = True) -> EvidenceByPlateResponse:
    normalized_plate = plate_text.strip().upper().replace(" ", "").replace("-", "")
    records = temporary_user_repository.list_by_plate(normalized_plate, include_expired=include_expired)
    return EvidenceByPlateResponse(plate_text=normalized_plate, count=len(records), temporary_users=records)
