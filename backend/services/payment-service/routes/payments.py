from fastapi import APIRouter

from schemas.payment import PaymentRequest, PaymentResponse, PaymentSessionResponse, PaymentStatusResponse
from services.payment_flow_service import PaymentFlowService


router = APIRouter(prefix="/payments", tags=["payments"])
payment_service = PaymentFlowService()


@router.get("/session/{plate}", response_model=PaymentSessionResponse)
def get_session_by_plate(plate: str) -> PaymentSessionResponse:
    return payment_service.get_session_by_plate(plate)


@router.get("/session-by-qr/{qr_code}", response_model=PaymentSessionResponse)
def get_session_by_qr(qr_code: str) -> PaymentSessionResponse:
    return payment_service.get_session_by_qr(qr_code)


@router.post("/pay", response_model=PaymentResponse)
def pay_session(payload: PaymentRequest) -> PaymentResponse:
    return payment_service.pay_session(payload)


@router.get("/status/{session_id}", response_model=PaymentStatusResponse)
def get_payment_status(session_id: str) -> PaymentStatusResponse:
    return payment_service.get_status(session_id)
