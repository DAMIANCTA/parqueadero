from fastapi import APIRouter, File, Form, HTTPException, UploadFile
import httpx

from schemas.integration import (
    CashierPaymentLookupResponse,
    CashierPaymentRegistrationRequest,
    CashierPaymentRegistrationResponse,
    DemoOpenGateRequest,
    DemoOpenGateResponse,
    EvidenceUploadResponse,
    FaceServiceConfigResponse,
    ParkingAuthorizationResponse,
    PlateDetectBatchRequest,
    PlateDetectBatchResponse,
    PlateDetectRequest,
    PlateDetectResponse,
    ParkingEntryRequest,
    ParkingExitRequest,
    PaymentByPlateRequest,
    PaymentByPlateResponse,
)
from security import require_permissions
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


@router.get("/payments/by-plate/{plate_text}", response_model=CashierPaymentLookupResponse)
def get_payment_by_plate(plate_text: str) -> CashierPaymentLookupResponse:
    try:
        response = integration_service.get_payment_by_plate(plate_text)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Payment service unavailable: {exc}") from exc
    return CashierPaymentLookupResponse(**response)


@router.post(
    "/payments/register-cash-payment",
    response_model=CashierPaymentRegistrationResponse,
    dependencies=[require_permissions("payments.pay")],
)
def register_cash_payment(payload: CashierPaymentRegistrationRequest) -> CashierPaymentRegistrationResponse:
    try:
        response = integration_service.register_cash_payment(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Payment service unavailable: {exc}") from exc
    return CashierPaymentRegistrationResponse(**response)


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


@router.post("/plates/detect-batch", response_model=PlateDetectBatchResponse)
def detect_plate_batch(payload: PlateDetectBatchRequest) -> PlateDetectBatchResponse:
    try:
        response = integration_service.proxy_plate_detection_batch(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Plate service unavailable: {exc}") from exc
    return PlateDetectBatchResponse(**response)


@router.get("/faces/config", response_model=FaceServiceConfigResponse)
def get_face_config() -> FaceServiceConfigResponse:
    try:
        response = integration_service.get_face_config()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Face service unavailable: {exc}") from exc
    return FaceServiceConfigResponse(**response)
