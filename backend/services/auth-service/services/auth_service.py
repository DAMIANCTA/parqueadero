from fastapi import HTTPException

from config import settings
from repositories.user_repository import UserRepository
from schemas.auth import CurrentUserResponse, LoginRequest, TokenResponse
from security import encode_access_token


ROLE_PERMISSIONS = {
    "superadmin": ["*"],
    "admin_university": [
        "gateway.catalog.read",
        "universities.read",
        "members.read",
        "members.write",
        "vehicles.read",
        "vehicles.write",
        "permits.read",
        "permits.write",
        "parking.entry",
        "parking.exit",
        "payments.read",
        "payments.pay",
        "faces.enroll",
        "faces.verify",
        "faces.compare",
        "faces.liveness_check",
        "plates.detect",
        "iot.gates.open",
        "audit.read",
        "auth.mock.read",
    ],
    "security": [
        "gateway.catalog.read",
        "universities.read",
        "members.read",
        "vehicles.read",
        "permits.read",
        "parking.entry",
        "parking.exit",
        "faces.enroll",
        "faces.verify",
        "faces.compare",
        "faces.liveness_check",
        "plates.detect",
        "audit.read",
    ],
    "cashier": ["payments.read", "payments.pay", "permits.read", "permits.write", "members.read", "vehicles.read"],
    "gate_operator": [
        "parking.entry",
        "parking.exit",
        "members.read",
        "vehicles.read",
        "permits.read",
        "faces.verify",
        "faces.compare",
        "faces.liveness_check",
        "plates.detect",
        "iot.gates.open",
    ],
    "student": [],
    "teacher": [],
    "employee": [],
    "visitor": [],
    "auditor": [
        "gateway.catalog.read",
        "universities.read",
        "members.read",
        "vehicles.read",
        "permits.read",
        "payments.read",
        "audit.read",
    ],
}


class AuthService:
    def __init__(self) -> None:
        self.repository = UserRepository()

    def issue_token(self, payload: LoginRequest) -> TokenResponse:
        user = self.repository.get_user(payload.username)
        if user is None or user["password"] != payload.password:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        permissions = self._permissions_for_roles(user["roles"])
        token = encode_access_token(
            secret_key=settings.jwt_secret_key,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            expires_minutes=settings.jwt_access_token_expires_minutes,
            claims={
                "sub": user["id"],
                "username": user["username"],
                "roles": user["roles"],
                "permissions": permissions,
                "university_id": user["university_id"],
            },
        )
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expires_minutes * 60,
            roles=user["roles"],
            permissions=permissions,
            university_id=user["university_id"],
        )

    def current_user(self, payload: dict) -> CurrentUserResponse:
        return CurrentUserResponse(
            sub=payload["sub"],
            username=payload["username"],
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
            university_id=payload.get("university_id"),
        )

    def _permissions_for_roles(self, roles: list[str]) -> list[str]:
        permissions: set[str] = set()
        for role in roles:
            permissions.update(ROLE_PERMISSIONS.get(role, []))
        return sorted(permissions)
