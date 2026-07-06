from fastapi import APIRouter, Request

from config import settings
from schemas.payment import (
    InternalSessionUpsertRequest,
    PaymentByPlateRequest,
    PaymentRequest,
    PaymentResponse,
    PaymentSessionResponse,
    PaymentStatusByPlateResponse,
    PaymentStatusResponse,
    SessionPaymentDetail,
)
from security import require_permissions, verify_internal_audit_key
from services.payment_flow_service import PaymentFlowService


router = APIRouter(prefix="/payments", tags=["payments"])
payment_service = PaymentFlowService()


@router.get("/session/{plate}", response_model=PaymentSessionResponse, dependencies=[require_permissions("payments.read")])
def get_session_by_plate(plate: str) -> PaymentSessionResponse:
    return payment_service.get_session_by_plate(plate)


@router.get("/session-by-qr/{qr_code}", response_model=PaymentSessionResponse, dependencies=[require_permissions("payments.read")])
def get_session_by_qr(qr_code: str) -> PaymentSessionResponse:
    return payment_service.get_session_by_qr(qr_code)


@router.post("/pay", response_model=PaymentResponse, dependencies=[require_permissions("payments.pay")])
def pay_session(payload: PaymentRequest) -> PaymentResponse:
    return payment_service.pay_session(payload)


@router.post("/pay-by-plate", response_model=PaymentResponse, dependencies=[require_permissions("payments.pay")])
def pay_session_by_plate(payload: PaymentByPlateRequest) -> PaymentResponse:
    return payment_service.pay_session_by_plate(payload)


@router.get("/status/{session_id}", response_model=PaymentStatusResponse, dependencies=[require_permissions("payments.read")])
def get_payment_status(session_id: str) -> PaymentStatusResponse:
    return payment_service.get_status(session_id)


@router.get("/internal/status-by-plate", response_model=PaymentStatusByPlateResponse)
def get_internal_payment_status_by_plate(request: Request, plate: str) -> PaymentStatusByPlateResponse:
    verify_internal_audit_key(request, settings.audit_internal_key)
    return payment_service.get_status_by_plate(plate)


@router.post("/internal/sessions/upsert", response_model=SessionPaymentDetail)
def upsert_internal_session(request: Request, payload: InternalSessionUpsertRequest) -> SessionPaymentDetail:
    verify_internal_audit_key(request, settings.audit_internal_key)
    return payment_service.upsert_internal_session(payload)
