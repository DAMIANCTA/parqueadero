from fastapi import APIRouter, Request

from schemas.auth import (
    CurrentUserResponse,
    DriverRegisterRequest,
    LoginRequest,
    TokenResponse,
    UniversityCreateRequest,
    UniversityListResponse,
    UniversityResponse,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
)
from security import get_request_user, require_permissions
from services.auth_service import AuthService


router = APIRouter(tags=["auth"])
auth_service = AuthService()


@router.post("/auth/login", response_model=TokenResponse)
@router.post("/api/v1/auth/login", response_model=TokenResponse)
@router.post("/auth/token", response_model=TokenResponse)
@router.post("/api/v1/auth/token", response_model=TokenResponse)
def issue_token(payload: LoginRequest) -> TokenResponse:
    return auth_service.issue_token(payload)


@router.post("/auth/register", response_model=TokenResponse)
@router.post("/api/v1/auth/register", response_model=TokenResponse)
def register_driver(payload: DriverRegisterRequest) -> TokenResponse:
    return auth_service.register_driver(payload)


@router.get("/auth/me", response_model=CurrentUserResponse)
@router.get("/api/v1/auth/me", response_model=CurrentUserResponse)
def me(request: Request) -> CurrentUserResponse:
    return auth_service.current_user(get_request_user(request))


@router.get(
    "/universities",
    response_model=UniversityListResponse,
    dependencies=[require_permissions("universities.read")],
)
def list_universities(request: Request) -> UniversityListResponse:
    return auth_service.list_universities(get_request_user(request))


@router.post(
    "/universities",
    response_model=UniversityResponse,
    dependencies=[require_permissions("universities.write")],
)
def create_university(request: Request, payload: UniversityCreateRequest) -> UniversityResponse:
    return auth_service.create_university(get_request_user(request), payload)


@router.get(
    "/users",
    response_model=UserListResponse,
    dependencies=[require_permissions("users.read")],
)
def list_users(request: Request, university_id: str | None = None, role: str | None = None) -> UserListResponse:
    return auth_service.list_users(get_request_user(request), university_id=university_id, role=role)


@router.post(
    "/users",
    response_model=UserResponse,
    dependencies=[require_permissions("users.write")],
)
def create_user(request: Request, payload: UserCreateRequest) -> UserResponse:
    return auth_service.create_user(get_request_user(request), payload)
