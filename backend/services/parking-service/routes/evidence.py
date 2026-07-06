from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from schemas.evidence import EvidenceUploadResponse, ImageType
from services.evidence_storage_service import EvidenceStorageService


router = APIRouter(prefix="/evidence", tags=["evidence"])
evidence_service = EvidenceStorageService()


@router.post("/upload", response_model=EvidenceUploadResponse)
async def upload_evidence(
    image_type: ImageType = Form(...),
    plate: str = Form(...),
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
            session_id=session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Evidence upload failed: {exc}") from exc
    return EvidenceUploadResponse(**evidence)
