from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
import httpx

from schemas.integration import (
    FaceEnrollMemberRequest,
    FaceProfileListResponse,
    FaceProfileResponse,
    AdminAuditEventListResponse,
    AdminDashboardSummaryResponse,
    AdminSessionListResponse,
    CashierPaymentLookupResponse,
    CashierPaymentRegistrationRequest,
    CashierPaymentRegistrationResponse,
    CurrentUserResponse,
    DemoOpenGateRequest,
    DemoOpenGateResponse,
    EvidenceUploadResponse,
    FaceServiceConfigResponse,
    GatewayTokenResponse,
    IotGateCommandRequest,
    IotGateCommandResponse,
    IotGateStatusResponse,
    LoginRequest,
    MemberAccessValidationRequest,
    MemberAccessValidationResponse,
    MemberCreateRequest,
    MemberListResponse,
    MemberResponse,
    MonthlyPermitCreateRequest,
    MonthlyPermitListResponse,
    MonthlyPermitResponse,
    ParkingAuthorizationResponse,
    PlateDetectBatchRequest,
    PlateDetectBatchResponse,
    PlateDetectRequest,
    PlateDetectResponse,
    ParkingEntryRequest,
    ParkingExitRequest,
    PermitLookupResponse,
    PaymentByPlateRequest,
    PaymentByPlateResponse,
    VehicleAuthorizationRequest,
    VehicleAuthorizationResponse,
    VehicleCreateRequest,
    VehicleListResponse,
    VehicleLookupResponse,
    VehicleResponse,
)
from security import require_permissions
from services.integration_service import IntegrationService


router = APIRouter(tags=["integration"])
integration_service = IntegrationService()


@router.post("/auth/token", response_model=GatewayTokenResponse)
def issue_token(payload: LoginRequest) -> GatewayTokenResponse:
    try:
        response = integration_service.issue_token(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {exc}") from exc
    return GatewayTokenResponse(**response)


@router.get("/auth/me", response_model=CurrentUserResponse)
def current_user(authorization: str | None = Header(default=None)) -> CurrentUserResponse:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.split(" ", 1)[1].strip()
    try:
        response = integration_service.get_current_user(token)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {exc}") from exc
    return CurrentUserResponse(**response)


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


@router.post("/iot/gates/{gate_id}/open", response_model=IotGateCommandResponse, dependencies=[require_permissions("iot.gates.open")])
def open_iot_gate(gate_id: str, payload: IotGateCommandRequest) -> IotGateCommandResponse:
    try:
        response = integration_service.open_iot_gate(gate_id, payload.model_dump())
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"IoT service unavailable: {exc}") from exc
    return IotGateCommandResponse(**response)


@router.post("/iot/gates/{gate_id}/deny", response_model=IotGateCommandResponse, dependencies=[require_permissions("iot.gates.deny")])
def deny_iot_gate(gate_id: str, payload: IotGateCommandRequest) -> IotGateCommandResponse:
    try:
        response = integration_service.deny_iot_gate(gate_id, payload.model_dump())
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"IoT service unavailable: {exc}") from exc
    return IotGateCommandResponse(**response)


@router.get("/iot/gates/status/{gate_id}", response_model=IotGateStatusResponse)
def get_iot_gate_status(gate_id: str) -> IotGateStatusResponse:
    try:
        response = integration_service.get_iot_gate_status(gate_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"IoT service unavailable: {exc}") from exc
    return IotGateStatusResponse(**response)


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


@router.get("/admin/dashboard-summary", response_model=AdminDashboardSummaryResponse)
def get_admin_dashboard_summary() -> AdminDashboardSummaryResponse:
    try:
        response = integration_service.get_admin_dashboard_summary()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Admin summary unavailable: {exc}") from exc
    return AdminDashboardSummaryResponse(**response)


@router.get("/admin/active-sessions", response_model=AdminSessionListResponse)
def get_admin_active_sessions() -> AdminSessionListResponse:
    try:
        response = integration_service.get_admin_active_sessions()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Active sessions unavailable: {exc}") from exc
    return AdminSessionListResponse(**response)


@router.get("/admin/session-history", response_model=AdminSessionListResponse)
def get_admin_session_history() -> AdminSessionListResponse:
    try:
        response = integration_service.get_admin_session_history()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Session history unavailable: {exc}") from exc
    return AdminSessionListResponse(**response)


@router.get("/admin/audit-events", response_model=AdminAuditEventListResponse)
def get_admin_audit_events() -> AdminAuditEventListResponse:
    try:
        response = integration_service.get_admin_audit_events()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Audit events unavailable: {exc}") from exc
    return AdminAuditEventListResponse(**response)


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


@router.post("/members", response_model=MemberResponse, dependencies=[require_permissions("members.write")])
def create_member(payload: MemberCreateRequest) -> MemberResponse:
    response = integration_service.create_member(payload)
    return MemberResponse(**response)


@router.get("/members", response_model=MemberListResponse, dependencies=[require_permissions("members.read")])
def list_members(university_id: str | None = None) -> MemberListResponse:
    response = integration_service.list_members(university_id)
    return MemberListResponse(**response)


@router.post("/vehicles", response_model=VehicleResponse, dependencies=[require_permissions("vehicles.write")])
def create_vehicle(payload: VehicleCreateRequest) -> VehicleResponse:
    response = integration_service.create_vehicle(payload)
    return VehicleResponse(**response)


@router.get("/vehicles", response_model=VehicleListResponse, dependencies=[require_permissions("vehicles.read")])
def list_vehicles(university_id: str | None = None) -> VehicleListResponse:
    response = integration_service.list_vehicles(university_id)
    return VehicleListResponse(**response)


@router.get("/vehicles/by-plate/{plate_text}", response_model=VehicleLookupResponse, dependencies=[require_permissions("vehicles.read")])
def get_vehicle_by_plate(plate_text: str) -> VehicleLookupResponse:
    response = integration_service.get_vehicle_by_plate(plate_text)
    return VehicleLookupResponse(**response)


@router.post("/members/{member_id}/faces/enroll", response_model=FaceProfileResponse, dependencies=[require_permissions("faces.enroll", "members.write")])
def enroll_member_face(member_id: str, payload: FaceEnrollMemberRequest) -> FaceProfileResponse:
    response = integration_service.enroll_member_face(member_id, payload)
    return FaceProfileResponse(**response)


@router.get("/members/faces", response_model=FaceProfileListResponse, dependencies=[require_permissions("members.read")])
def list_face_profiles(university_id: str | None = None) -> FaceProfileListResponse:
    response = integration_service.list_face_profiles(university_id)
    return FaceProfileListResponse(**response)


@router.get("/members/{member_id}", response_model=MemberResponse, dependencies=[require_permissions("members.read")])
def get_member(member_id: str) -> MemberResponse:
    response = integration_service.get_member(member_id)
    return MemberResponse(**response)


@router.post("/vehicles/{vehicle_id}/authorize-person", response_model=VehicleAuthorizationResponse, dependencies=[require_permissions("vehicles.write", "members.write")])
def authorize_vehicle_person(vehicle_id: str, payload: VehicleAuthorizationRequest) -> VehicleAuthorizationResponse:
    response = integration_service.authorize_vehicle_person(vehicle_id, payload)
    return VehicleAuthorizationResponse(**response)


@router.post("/permits/monthly", response_model=MonthlyPermitResponse, dependencies=[require_permissions("permits.write")])
def create_monthly_permit(payload: MonthlyPermitCreateRequest) -> MonthlyPermitResponse:
    response = integration_service.create_monthly_permit(payload)
    return MonthlyPermitResponse(**response)


@router.get("/permits/monthly", response_model=MonthlyPermitListResponse, dependencies=[require_permissions("permits.read")])
def list_monthly_permits(university_id: str | None = None) -> MonthlyPermitListResponse:
    response = integration_service.list_monthly_permits(university_id)
    return MonthlyPermitListResponse(**response)


@router.get("/permits/by-plate/{plate_text}", response_model=PermitLookupResponse, dependencies=[require_permissions("permits.read")])
def get_permit_by_plate(plate_text: str) -> PermitLookupResponse:
    response = integration_service.get_permit_by_plate(plate_text)
    return PermitLookupResponse(**response)


@router.post("/access/validate-member-entry", response_model=MemberAccessValidationResponse, dependencies=[require_permissions("members.read")])
def validate_member_entry(payload: MemberAccessValidationRequest) -> MemberAccessValidationResponse:
    response = integration_service.validate_member_entry(payload)
    return MemberAccessValidationResponse(**response)
