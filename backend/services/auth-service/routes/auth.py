from fastapi import APIRouter, Request

from schemas.auth import CurrentUserResponse, LoginRequest, TokenResponse
from services.auth_service import AuthService
from security import get_request_user


router = APIRouter(tags=["auth"])
auth_service = AuthService()


@router.post("/auth/token", response_model=TokenResponse)
@router.post("/api/v1/auth/token", response_model=TokenResponse)
def issue_token(payload: LoginRequest) -> TokenResponse:
    return auth_service.issue_token(payload)


@router.get("/auth/me", response_model=CurrentUserResponse)
@router.get("/api/v1/auth/me", response_model=CurrentUserResponse)
def me(request: Request) -> CurrentUserResponse:
    return auth_service.current_user(get_request_user(request))
