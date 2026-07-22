from fastapi import APIRouter, File, Form, Header, HTTPException, Request, Response, UploadFile
import httpx

from schemas.integration import (
    AccessHistoryListResponse,
    ActiveSessionResponse,
    DriverRegisterRequest,
    EvidenceForensicResponse,
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
    MyVehicleCreateRequest,
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
    UniversityCreateRequest,
    UniversityListResponse,
    UniversityResponse,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    VehicleAuthorizationRequest,
    VehicleAuthorizationResponse,
    VehicleCreateRequest,
    VehicleListResponse,
    VehicleLookupResponse,
    VehicleResponse,
)
from security import get_request_user, require_permissions, resolve_university_scope
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


@router.post("/auth/login", response_model=GatewayTokenResponse)
def issue_login(payload: LoginRequest) -> GatewayTokenResponse:
    try:
        response = integration_service.issue_login(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {exc}") from exc
    return GatewayTokenResponse(**response)


@router.get("/auth/me", response_model=CurrentUserResponse)
def current_user(authorization: str | None = Header(default=None)) -> CurrentUserResponse:
    token = _extract_bearer_token(authorization)
    try:
        response = integration_service.get_current_user(token)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {exc}") from exc
    return CurrentUserResponse(**response)


@router.post("/auth/register", response_model=GatewayTokenResponse)
def register_driver(payload: DriverRegisterRequest) -> GatewayTokenResponse:
    try:
        response = integration_service.register_driver(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Auth service unavailable: {exc}") from exc
    return GatewayTokenResponse(**response)


@router.get("/universities", response_model=UniversityListResponse, dependencies=[require_permissions("universities.read")])
def list_universities(authorization: str | None = Header(default=None)) -> UniversityListResponse:
    token = _extract_bearer_token(authorization)
    response = integration_service.list_universities(token)
    return UniversityListResponse(**response)


@router.post("/universities", response_model=UniversityResponse, dependencies=[require_permissions("universities.write")])
def create_university(payload: UniversityCreateRequest, authorization: str | None = Header(default=None)) -> UniversityResponse:
    token = _extract_bearer_token(authorization)
    response = integration_service.create_university(payload, token)
    return UniversityResponse(**response)


@router.get("/users", response_model=UserListResponse, dependencies=[require_permissions("users.read")])
def list_users(
    request: Request,
    authorization: str | None = Header(default=None),
    university_id: str | None = None,
    role: str | None = None,
) -> UserListResponse:
    user = get_request_user(request)
    scoped_university_id = resolve_university_scope(user, university_id)
    token = _extract_bearer_token(authorization)
    response = integration_service.list_users(token, university_id=scoped_university_id, role=role)
    return UserListResponse(**response)


@router.post("/users", response_model=UserResponse, dependencies=[require_permissions("users.write")])
def create_user(
    request: Request,
    payload: UserCreateRequest,
    authorization: str | None = Header(default=None),
) -> UserResponse:
    user = get_request_user(request)
    scoped_university_id = payload.university_id
    if payload.university_id is not None or "*" not in set(user.get("permissions", [])):
        scoped_university_id = resolve_university_scope(user, payload.university_id)
    token = _extract_bearer_token(authorization)
    response = integration_service.create_user(payload.model_copy(update={"university_id": scoped_university_id}), token)
    return UserResponse(**response)


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


@router.get("/iot/gates/status/{gate_id}", response_model=IotGateStatusResponse, dependencies=[require_permissions("iot.gates.read")])
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


@router.get("/payments/by-plate/{plate_text}", response_model=CashierPaymentLookupResponse, dependencies=[require_permissions("payments.read")])
def get_payment_by_plate(request: Request, plate_text: str) -> CashierPaymentLookupResponse:
    try:
        user = get_request_user(request)
        response = integration_service.get_payment_by_plate(plate_text, resolve_university_scope(user, None))
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


@router.get("/admin/dashboard-summary", response_model=AdminDashboardSummaryResponse, dependencies=[require_permissions("dashboard.read")])
def get_admin_dashboard_summary(request: Request) -> AdminDashboardSummaryResponse:
    try:
        user = get_request_user(request)
        response = integration_service.get_admin_dashboard_summary(resolve_university_scope(user, None))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Admin summary unavailable: {exc}") from exc
    return AdminDashboardSummaryResponse(**response)


@router.get("/admin/active-sessions", response_model=AdminSessionListResponse, dependencies=[require_permissions("sessions.read")])
def get_admin_active_sessions(request: Request) -> AdminSessionListResponse:
    try:
        user = get_request_user(request)
        response = integration_service.get_admin_active_sessions(resolve_university_scope(user, None))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Active sessions unavailable: {exc}") from exc
    return AdminSessionListResponse(**response)


@router.get("/admin/session-history", response_model=AdminSessionListResponse, dependencies=[require_permissions("history.read")])
def get_admin_session_history(request: Request) -> AdminSessionListResponse:
    try:
        user = get_request_user(request)
        response = integration_service.get_admin_session_history(resolve_university_scope(user, None))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Session history unavailable: {exc}") from exc
    return AdminSessionListResponse(**response)


@router.get("/admin/audit-events", response_model=AdminAuditEventListResponse, dependencies=[require_permissions("audit.read")])
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
    university_id: str | None = Form(default=None),
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
            university_id=university_id,
            session_id=session_id,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Parking service unavailable: {exc}") from exc
    return EvidenceUploadResponse(**response)


@router.get("/admin/access-history", response_model=AccessHistoryListResponse, dependencies=[require_permissions("history.read")])
def get_admin_access_history(request: Request) -> AccessHistoryListResponse:
    try:
        user = get_request_user(request)
        response = integration_service.get_parking_history(resolve_university_scope(user, None))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Access history unavailable: {exc}") from exc
    return AccessHistoryListResponse(**response)


def _resolve_my_plate(user: dict) -> str | None:
    vehicles = integration_service.list_my_vehicles(user["sub"])
    if not vehicles["items"]:
        return None
    return vehicles["items"][0]["plate_text"]


@router.get(
    "/parking/mine/active-session",
    response_model=ActiveSessionResponse,
    dependencies=[require_permissions("parking.self_read")],
)
def get_my_active_session(request: Request) -> ActiveSessionResponse:
    user = get_request_user(request)
    try:
        plate_text = _resolve_my_plate(user)
        if plate_text is None:
            return ActiveSessionResponse(plate_text="", active=False)
        response = integration_service.get_my_active_session(plate_text)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Parking service unavailable: {exc}") from exc
    return ActiveSessionResponse(**response)


@router.get(
    "/parking/mine/history",
    response_model=AccessHistoryListResponse,
    dependencies=[require_permissions("parking.self_read")],
)
def get_my_history(request: Request, limit: int = 100) -> AccessHistoryListResponse:
    user = get_request_user(request)
    try:
        plate_text = _resolve_my_plate(user)
        if plate_text is None:
            return AccessHistoryListResponse(total=0, items=[])
        response = integration_service.get_my_history(plate_text, limit=limit)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Parking history unavailable: {exc}") from exc
    return AccessHistoryListResponse(**response)


@router.get("/evidence/image/{image_id}", dependencies=[require_permissions("evidence.read")])
def get_evidence_image(image_id: str) -> Response:
    try:
        payload, content_type = integration_service.get_evidence_image_bytes(image_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Evidence image unavailable: {exc}") from exc
    return Response(content=payload, media_type=content_type)


@router.get("/evidence/by-plate/{plate_text}", response_model=EvidenceForensicResponse, dependencies=[require_permissions("evidence.read")])
def get_evidence_by_plate(plate_text: str, include_expired: bool = True) -> EvidenceForensicResponse:
    try:
        response = integration_service.get_evidence_by_plate(plate_text, include_expired=include_expired)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Evidence lookup unavailable: {exc}") from exc
    return EvidenceForensicResponse(**response)


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
def create_member(request: Request, payload: MemberCreateRequest) -> MemberResponse:
    user = get_request_user(request)
    response = integration_service.create_member(
        payload.model_copy(update={"university_id": resolve_university_scope(user, payload.university_id)})
    )
    return MemberResponse(**response)


@router.get("/members", response_model=MemberListResponse, dependencies=[require_permissions("members.read")])
def list_members(request: Request, university_id: str | None = None) -> MemberListResponse:
    user = get_request_user(request)
    response = integration_service.list_members(resolve_university_scope(user, university_id))
    return MemberListResponse(**response)


@router.post("/vehicles", response_model=VehicleResponse, dependencies=[require_permissions("vehicles.write")])
def create_vehicle(request: Request, payload: VehicleCreateRequest) -> VehicleResponse:
    user = get_request_user(request)
    response = integration_service.create_vehicle(
        payload.model_copy(update={"university_id": resolve_university_scope(user, payload.university_id)})
    )
    return VehicleResponse(**response)


@router.get("/vehicles", response_model=VehicleListResponse, dependencies=[require_permissions("vehicles.read")])
def list_vehicles(request: Request, university_id: str | None = None) -> VehicleListResponse:
    user = get_request_user(request)
    response = integration_service.list_vehicles(resolve_university_scope(user, university_id))
    return VehicleListResponse(**response)


@router.get("/vehicles/mine", response_model=VehicleListResponse, dependencies=[require_permissions("vehicles.self_manage")])
def list_my_vehicles(request: Request) -> VehicleListResponse:
    user = get_request_user(request)
    try:
        response = integration_service.list_my_vehicles(user["sub"])
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Vehicle service unavailable: {exc}") from exc
    return VehicleListResponse(**response)


@router.post("/vehicles/mine", response_model=VehicleResponse, dependencies=[require_permissions("vehicles.self_manage")])
def register_my_vehicle(request: Request, payload: MyVehicleCreateRequest) -> VehicleResponse:
    user = get_request_user(request)
    university_id = resolve_university_scope(user, None)
    try:
        response = integration_service.register_my_vehicle(user, payload, university_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Vehicle service unavailable: {exc}") from exc
    return VehicleResponse(**response)


@router.get(
    "/vehicles/mine/authorized-drivers",
    response_model=VehicleLookupResponse,
    dependencies=[require_permissions("vehicles.self_manage")],
)
def list_my_authorized_drivers(request: Request) -> VehicleLookupResponse:
    user = get_request_user(request)
    try:
        vehicles = integration_service.list_my_vehicles(user["sub"])
        if not vehicles["items"]:
            return VehicleLookupResponse(found=False, message="No vehicle registered yet")
        response = integration_service.get_vehicle_by_plate(vehicles["items"][0]["plate_text"])
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Vehicle service unavailable: {exc}") from exc
    return VehicleLookupResponse(**response)


@router.get("/vehicles/by-plate/{plate_text}", response_model=VehicleLookupResponse, dependencies=[require_permissions("vehicles.read")])
def get_vehicle_by_plate(plate_text: str) -> VehicleLookupResponse:
    response = integration_service.get_vehicle_by_plate(plate_text)
    return VehicleLookupResponse(**response)


@router.post("/members/{member_id}/faces/enroll", response_model=FaceProfileResponse, dependencies=[require_permissions("faces.enroll", "members.write")])
def enroll_member_face(member_id: str, payload: FaceEnrollMemberRequest) -> FaceProfileResponse:
    response = integration_service.enroll_member_face(member_id, payload)
    return FaceProfileResponse(**response)


@router.get("/members/faces", response_model=FaceProfileListResponse, dependencies=[require_permissions("faces.read")])
def list_face_profiles(request: Request, university_id: str | None = None) -> FaceProfileListResponse:
    user = get_request_user(request)
    response = integration_service.list_face_profiles(resolve_university_scope(user, university_id))
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
def create_monthly_permit(request: Request, payload: MonthlyPermitCreateRequest) -> MonthlyPermitResponse:
    user = get_request_user(request)
    response = integration_service.create_monthly_permit(
        payload.model_copy(update={"university_id": resolve_university_scope(user, payload.university_id)})
    )
    return MonthlyPermitResponse(**response)


@router.get("/permits/monthly", response_model=MonthlyPermitListResponse, dependencies=[require_permissions("permits.read")])
def list_monthly_permits(request: Request, university_id: str | None = None) -> MonthlyPermitListResponse:
    user = get_request_user(request)
    response = integration_service.list_monthly_permits(resolve_university_scope(user, university_id))
    return MonthlyPermitListResponse(**response)


@router.get("/permits/by-plate/{plate_text}", response_model=PermitLookupResponse, dependencies=[require_permissions("permits.read")])
def get_permit_by_plate(plate_text: str) -> PermitLookupResponse:
    response = integration_service.get_permit_by_plate(plate_text)
    return PermitLookupResponse(**response)


@router.post("/access/validate-member-entry", response_model=MemberAccessValidationResponse, dependencies=[require_permissions("members.read")])
def validate_member_entry(payload: MemberAccessValidationRequest) -> MemberAccessValidationResponse:
    response = integration_service.validate_member_entry(payload)
    return MemberAccessValidationResponse(**response)


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    return authorization.split(" ", 1)[1].strip()
