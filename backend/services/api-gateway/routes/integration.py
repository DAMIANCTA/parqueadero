from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import httpx

from schemas.integration import (
    DemoOpenGateRequest,
    DemoOpenGateResponse,
    EvidenceUploadResponse,
    ParkingAuthorizationResponse,
    PlateDetectRequest,
    PlateDetectResponse,
    ParkingEntryRequest,
    ParkingExitRequest,
    PaymentByPlateRequest,
    PaymentByPlateResponse,
)
from services.integration_service import IntegrationService


router = APIRouter(tags=["integration"])
integration_service = IntegrationService()


@router.post("/parking/entry", response_model=ParkingAuthorizationResponse)
def gateway_entry(payload: ParkingEntryRequest) -> ParkingAuthorizationResponse:
    try:
        response = integration_service.proxy_entry(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Parking service unavailable: {exc}") from exc
    return ParkingAuthorizationResponse(**response)


@router.post("/parking/exit", response_model=ParkingAuthorizationResponse)
def gateway_exit(payload: ParkingExitRequest) -> ParkingAuthorizationResponse:
    try:
        response = integration_service.proxy_exit(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Parking service unavailable: {exc}") from exc
    return ParkingAuthorizationResponse(**response)


@router.post("/demo/open-gate", response_model=DemoOpenGateResponse)
def demo_open_gate(payload: DemoOpenGateRequest) -> DemoOpenGateResponse:
    try:
        response = integration_service.open_demo_gate(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"IoT service unavailable: {exc}") from exc
    return DemoOpenGateResponse(**response)


@router.post("/payments/pay-by-plate", response_model=PaymentByPlateResponse)
def pay_by_plate(payload: PaymentByPlateRequest) -> PaymentByPlateResponse:
    try:
        response = integration_service.pay_session_by_plate(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Payment service unavailable: {exc}") from exc
    return PaymentByPlateResponse(**response)


@router.post("/evidence/upload", response_model=EvidenceUploadResponse)
async def upload_evidence(
    image_type: str = Form(...),
    plate: str = Form(...),
    session_id: str | None = Form(default=None),
    file: UploadFile = File(...),
) -> EvidenceUploadResponse:
    try:
        response = integration_service.proxy_evidence_upload(
            file_bytes=await file.read(),
            filename=file.filename or "evidence.bin",
            content_type=file.content_type or "application/octet-stream",
            image_type=image_type,
            plate=plate,
            session_id=session_id,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Parking service unavailable: {exc}") from exc
    return EvidenceUploadResponse(**response)


@router.post("/plates/detect", response_model=PlateDetectResponse)
def detect_plate(payload: PlateDetectRequest) -> PlateDetectResponse:
    try:
        response = integration_service.proxy_plate_detection(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Plate service unavailable: {exc}") from exc
    return PlateDetectResponse(**response)
