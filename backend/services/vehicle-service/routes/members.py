from fastapi import APIRouter, Request

from config import settings
from schemas.members import (
    FaceEnrollMemberRequest,
    FaceProfileListResponse,
    FaceProfileResponse,
    MemberAccessValidationRequest,
    MemberAccessValidationResponse,
    MemberCreateRequest,
    MemberListResponse,
    MemberResponse,
    MonthlyPermitCreateRequest,
    MonthlyPermitListResponse,
    MonthlyPermitResponse,
    PermitLookupResponse,
    RegisterOwnedVehicleRequest,
    VehicleAuthorizationRequest,
    VehicleAuthorizationResponse,
    VehicleCreateRequest,
    VehicleListResponse,
    VehicleLookupResponse,
    VehicleResponse,
    VehicleUpdateRequest,
)
from security import require_permissions, verify_internal_audit_key
from services.member_access_service import MemberAccessService


router = APIRouter(tags=["members"])
member_service = MemberAccessService()


@router.post("/members", response_model=MemberResponse, dependencies=[require_permissions("members.write")])
def create_member(payload: MemberCreateRequest) -> MemberResponse:
    return member_service.create_member(payload)


@router.get("/members", response_model=MemberListResponse, dependencies=[require_permissions("members.read")])
def list_members(university_id: str | None = None) -> MemberListResponse:
    return member_service.list_members(university_id)


@router.post("/vehicles", response_model=VehicleResponse, dependencies=[require_permissions("vehicles.write")])
def create_vehicle(payload: VehicleCreateRequest) -> VehicleResponse:
    return member_service.create_vehicle(payload)


@router.get("/vehicles", response_model=VehicleListResponse, dependencies=[require_permissions("vehicles.read")])
def list_vehicles(university_id: str | None = None) -> VehicleListResponse:
    return member_service.list_vehicles(university_id)


@router.get("/vehicles/by-plate/{plate_text}", response_model=VehicleLookupResponse, dependencies=[require_permissions("vehicles.read")])
def get_vehicle_by_plate(plate_text: str) -> VehicleLookupResponse:
    return member_service.get_vehicle_by_plate(plate_text)


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleResponse, dependencies=[require_permissions("vehicles.write")])
def update_vehicle(vehicle_id: str, payload: VehicleUpdateRequest) -> VehicleResponse:
    return member_service.update_vehicle(vehicle_id, payload)


@router.get(
    "/members/by-user/{user_id}/vehicles",
    response_model=VehicleListResponse,
    dependencies=[require_permissions("members.read", "vehicles.read")],
)
def list_vehicles_by_user(user_id: str) -> VehicleListResponse:
    return member_service.list_vehicles_by_user(user_id)


@router.get(
    "/members/by-user/{user_id}",
    response_model=MemberResponse,
    dependencies=[require_permissions("members.read")],
)
def get_member_by_user(user_id: str) -> MemberResponse:
    return member_service.get_member_by_user(user_id)


@router.post(
    "/vehicles/register-owned",
    response_model=VehicleResponse,
    dependencies=[require_permissions("vehicles.write", "members.write")],
)
def register_owned_vehicle(payload: RegisterOwnedVehicleRequest) -> VehicleResponse:
    return member_service.register_owned_vehicle(payload)


@router.post("/members/{member_id}/faces/enroll", response_model=FaceProfileResponse, dependencies=[require_permissions("faces.enroll", "members.write")])
def enroll_member_face(member_id: str, payload: FaceEnrollMemberRequest) -> FaceProfileResponse:
    return member_service.enroll_face(member_id, payload)


@router.get("/members/faces", response_model=FaceProfileListResponse, dependencies=[require_permissions("members.read")])
def list_face_profiles(university_id: str | None = None) -> FaceProfileListResponse:
    return member_service.list_face_profiles(university_id)


@router.get("/members/{member_id}", response_model=MemberResponse, dependencies=[require_permissions("members.read")])
def get_member(member_id: str) -> MemberResponse:
    return member_service.get_member(member_id)


@router.post("/vehicles/{vehicle_id}/authorize-person", response_model=VehicleAuthorizationResponse, dependencies=[require_permissions("vehicles.write", "members.write")])
def authorize_person(vehicle_id: str, payload: VehicleAuthorizationRequest) -> VehicleAuthorizationResponse:
    return member_service.authorize_person(vehicle_id, payload)


@router.post("/permits/monthly", response_model=MonthlyPermitResponse, dependencies=[require_permissions("permits.write")])
def create_monthly_permit(payload: MonthlyPermitCreateRequest) -> MonthlyPermitResponse:
    return member_service.create_monthly_permit(payload)


@router.get("/permits/monthly", response_model=MonthlyPermitListResponse, dependencies=[require_permissions("permits.read")])
def list_monthly_permits(university_id: str | None = None) -> MonthlyPermitListResponse:
    return member_service.list_monthly_permits(university_id)


@router.get("/permits/by-plate/{plate_text}", response_model=PermitLookupResponse, dependencies=[require_permissions("permits.read")])
def get_permit_by_plate(plate_text: str) -> PermitLookupResponse:
    return member_service.get_permit_by_plate(plate_text)


@router.post("/access/validate-member-entry", response_model=MemberAccessValidationResponse, dependencies=[require_permissions("members.read")])
def validate_member_entry(payload: MemberAccessValidationRequest) -> MemberAccessValidationResponse:
    return member_service.validate_member_access(payload)


@router.post("/internal/access/validate-member-entry", response_model=MemberAccessValidationResponse)
def validate_member_entry_internal(request: Request, payload: MemberAccessValidationRequest) -> MemberAccessValidationResponse:
    verify_internal_audit_key(request, settings.audit_internal_key)
    return member_service.validate_member_access(payload)


@router.post("/internal/access/validate-member-exit", response_model=MemberAccessValidationResponse)
def validate_member_exit_internal(request: Request, payload: MemberAccessValidationRequest) -> MemberAccessValidationResponse:
    verify_internal_audit_key(request, settings.audit_internal_key)
    return member_service.validate_member_access(payload)


@router.get("/internal/vehicles/by-plate/{plate_text}", response_model=VehicleLookupResponse)
def get_vehicle_by_plate_internal(request: Request, plate_text: str) -> VehicleLookupResponse:
    verify_internal_audit_key(request, settings.audit_internal_key)
    return member_service.get_vehicle_by_plate(plate_text)
