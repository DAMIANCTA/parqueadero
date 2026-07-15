from fastapi import APIRouter, HTTPException, Request

from config import settings
from schemas.payment import (
    AdminDashboardSummaryResponse,
    AdminSessionListResponse,
    CashierPaymentLookupResponse,
    CashierPaymentRegistrationRequest,
    CashierPaymentRegistrationResponse,
    InternalSessionCloseRequest,
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


@router.get("/by-plate/{plate_text}", response_model=CashierPaymentLookupResponse, dependencies=[require_permissions("payments.read")])
def get_active_payment_by_plate(plate_text: str, university_id: str | None = None) -> CashierPaymentLookupResponse:
    response = payment_service.get_active_payment_by_plate(plate_text, university_id=university_id)
    if not response.found:
        raise HTTPException(status_code=404, detail=response.message)
    return response


@router.get("/admin/dashboard-summary", response_model=AdminDashboardSummaryResponse, dependencies=[require_permissions("payments.read")])
def get_admin_dashboard_summary(university_id: str | None = None) -> AdminDashboardSummaryResponse:
    return payment_service.get_admin_dashboard_summary(university_id=university_id)


@router.get("/admin/active-sessions", response_model=AdminSessionListResponse, dependencies=[require_permissions("payments.read")])
def get_admin_active_sessions(university_id: str | None = None) -> AdminSessionListResponse:
    return payment_service.get_admin_active_sessions(university_id=university_id)


@router.get("/admin/session-history", response_model=AdminSessionListResponse, dependencies=[require_permissions("payments.read")])
def get_admin_session_history(university_id: str | None = None) -> AdminSessionListResponse:
    return payment_service.get_admin_session_history(university_id=university_id)


@router.post("/pay", response_model=PaymentResponse, dependencies=[require_permissions("payments.pay")])
def pay_session(payload: PaymentRequest) -> PaymentResponse:
    return payment_service.pay_session(payload)


@router.post("/register-cash-payment", response_model=CashierPaymentRegistrationResponse, dependencies=[require_permissions("payments.pay")])
def register_cash_payment(payload: CashierPaymentRegistrationRequest) -> CashierPaymentRegistrationResponse:
    return payment_service.register_cash_payment(payload)


@router.post("/pay-by-plate", response_model=PaymentResponse, dependencies=[require_permissions("payments.pay")])
def pay_session_by_plate(payload: PaymentByPlateRequest) -> PaymentResponse:
    return payment_service.pay_session_by_plate(payload)


@router.get("/status/{session_id}", response_model=PaymentStatusResponse, dependencies=[require_permissions("payments.read")])
def get_payment_status(session_id: str) -> PaymentStatusResponse:
    return payment_service.get_status(session_id)


@router.get("/internal/status-by-plate", response_model=PaymentStatusByPlateResponse)
def get_internal_payment_status_by_plate(request: Request, plate: str, university_id: str | None = None) -> PaymentStatusByPlateResponse:
    verify_internal_audit_key(request, settings.audit_internal_key)
    return payment_service.get_status_by_plate(plate, university_id=university_id)


@router.post("/internal/sessions/upsert", response_model=SessionPaymentDetail)
def upsert_internal_session(request: Request, payload: InternalSessionUpsertRequest) -> SessionPaymentDetail:
    verify_internal_audit_key(request, settings.audit_internal_key)
    return payment_service.upsert_internal_session(payload)


@router.post("/internal/sessions/close", response_model=SessionPaymentDetail)
def close_internal_session(request: Request, payload: InternalSessionCloseRequest) -> SessionPaymentDetail:
    verify_internal_audit_key(request, settings.audit_internal_key)
    return payment_service.close_internal_session(payload)
