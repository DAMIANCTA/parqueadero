from fastapi import HTTPException

from config import settings
from repositories.user_repository import UserRepository
from schemas.auth import (
    AuthenticatedUserResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
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
from security import encode_access_token


ROLE_PERMISSIONS = {
    "SUPER_ADMIN": ["*"],
    "UNIVERSITY_ADMIN": [
        "dashboard.read",
        "sessions.read",
        "history.read",
        "evidence.read",
        "audit.read",
        "universities.read",
        "users.read",
        "users.write",
        "members.read",
        "members.write",
        "vehicles.read",
        "vehicles.write",
        "permits.read",
        "permits.write",
        "faces.read",
        "faces.enroll",
        "faces.verify",
        "faces.compare",
        "faces.liveness_check",
        "payments.read",
        "payments.pay",
        "iot.gates.read",
        "iot.gates.open",
        "iot.gates.deny",
        "plates.detect",
    ],
    "CASHIER": [
        "payments.read",
        "payments.pay",
        "history.read",
    ],
    "MEMBER_MANAGER": [
        "members.read",
        "members.write",
        "vehicles.read",
        "vehicles.write",
        "permits.read",
        "permits.write",
        "faces.read",
        "faces.enroll",
        "faces.verify",
        "plates.detect",
    ],
    "SECURITY": [
        "sessions.read",
        "history.read",
        "evidence.read",
        "iot.gates.read",
        "iot.gates.open",
        "iot.gates.deny",
        "plates.detect",
        "faces.verify",
        "faces.compare",
        "faces.liveness_check",
    ],
    "AUDITOR": [
        "dashboard.read",
        "history.read",
        "evidence.read",
        "audit.read",
        "sessions.read",
        "payments.read",
    ],
    "DRIVER": [
        "vehicles.self_manage",
        "parking.self_read",
    ],
}


class AuthService:
    def __init__(self) -> None:
        self.repository = UserRepository()

    def issue_token(self, payload: LoginRequest) -> TokenResponse:
        user = self.repository.get_user(payload.username)
        if user is None or not self.repository.verify_password(user, payload.password):
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
                "full_name": user["full_name"],
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
            user=self._to_authenticated_user(user, permissions),
        )

    def current_user(self, payload: dict) -> CurrentUserResponse:
        user = self.repository.get_user(payload["username"])
        permissions = payload.get("permissions", [])
        if user is None:
            return CurrentUserResponse(
                sub=payload["sub"],
                id=payload["sub"],
                username=payload["username"],
                full_name=payload["username"],
                email=None,
                role=(payload.get("roles") or ["UNKNOWN"])[0],
                roles=payload.get("roles", []),
                permissions=permissions,
                university_id=payload.get("university_id"),
                status="ACTIVE",
            )
        return CurrentUserResponse(
            sub=payload["sub"],
            **self._to_authenticated_user(user, permissions).model_dump(),
        )

    def list_universities(self, actor: dict) -> UniversityListResponse:
        actor_role = self._primary_role(actor.get("roles", []))
        items = self.repository.list_universities(
            actor_role=actor_role,
            actor_university_id=actor.get("university_id"),
        )
        return UniversityListResponse(
            total=len(items),
            items=[self._to_university_response(item) for item in items],
        )

    def create_university(self, actor: dict, payload: UniversityCreateRequest) -> UniversityResponse:
        actor_role = self._primary_role(actor.get("roles", []))
        if actor_role != "SUPER_ADMIN":
            raise HTTPException(status_code=403, detail="Only SUPER_ADMIN can create universities")
        try:
            record = self.repository.create_university(payload.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return self._to_university_response(record)

    def list_users(self, actor: dict, university_id: str | None = None, role: str | None = None) -> UserListResponse:
        actor_role = self._primary_role(actor.get("roles", []))
        items = self.repository.list_users(
            actor_role=actor_role,
            actor_university_id=actor.get("university_id"),
            university_id=university_id,
            role=role,
        )
        return UserListResponse(
            total=len(items),
            items=[self._to_user_response(item) for item in items],
        )

    def create_user(self, actor: dict, payload: UserCreateRequest) -> UserResponse:
        actor_role = self._primary_role(actor.get("roles", []))
        target_role = payload.role.strip().upper()
        if actor_role == "UNIVERSITY_ADMIN" and target_role not in {"CASHIER", "MEMBER_MANAGER", "SECURITY", "AUDITOR"}:
            raise HTTPException(status_code=403, detail="UNIVERSITY_ADMIN can only create internal university roles")
        try:
            record = self.repository.create_user(
                payload.model_dump(),
                actor_role=actor_role,
                actor_university_id=actor.get("university_id"),
            )
        except ValueError as exc:
            detail = str(exc)
            status_code = 404 if "not found" in detail.lower() else 409
            raise HTTPException(status_code=status_code, detail=detail) from exc
        return self._to_user_response(record)

    def register_driver(self, payload: DriverRegisterRequest) -> TokenResponse:
        university_id = payload.university_id or self.repository.UCE_ID
        create_payload = {
            "username": payload.username,
            "password": payload.password,
            "full_name": payload.full_name,
            "email": payload.email,
            "role": "DRIVER",
            "university_id": university_id,
            "document_number": payload.document_number,
            "phone": payload.phone,
        }
        try:
            # actor_role="SUPER_ADMIN" solo habilita el passthrough del
            # university_id elegido por el propio registro publico; el rol
            # queda fijo en "DRIVER" arriba, sin importar el actor.
            self.repository.create_user(create_payload, actor_role="SUPER_ADMIN", actor_university_id=None)
        except ValueError as exc:
            detail = str(exc)
            status_code = 404 if "not found" in detail.lower() else 409
            raise HTTPException(status_code=status_code, detail=detail) from exc
        return self.issue_token(LoginRequest(username=payload.username, password=payload.password))

    def _permissions_for_roles(self, roles: list[str]) -> list[str]:
        permissions: set[str] = set()
        for role in roles:
            permissions.update(ROLE_PERMISSIONS.get(role, []))
        return sorted(permissions)

    @staticmethod
    def _primary_role(roles: list[str]) -> str:
        return roles[0] if roles else "UNKNOWN"

    def _to_authenticated_user(self, user: dict, permissions: list[str]) -> AuthenticatedUserResponse:
        return AuthenticatedUserResponse(
            id=user["id"],
            username=user["username"],
            full_name=user["full_name"],
            email=user.get("email"),
            document_number=user.get("document_number"),
            phone=user.get("phone"),
            role=user["role"],
            roles=user["roles"],
            university_id=user.get("university_id"),
            permissions=permissions,
            status=user.get("status", "ACTIVE"),
        )

    def change_password(self, actor: dict, payload: ChangePasswordRequest) -> ChangePasswordResponse:
        user = self.repository.get_user(actor["username"])
        if user is None or not self.repository.verify_password(user, payload.current_password):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        self.repository.set_password(actor["username"], payload.new_password)
        return ChangePasswordResponse(changed=True)

    @staticmethod
    def _to_university_response(record: dict) -> UniversityResponse:
        return UniversityResponse(
            id=record["id"],
            name=record["name"],
            code=record["code"],
            city=record["city"],
            status=record["status"],
            created_at=record["created_at"].isoformat(),
        )

    @staticmethod
    def _to_user_response(record: dict) -> UserResponse:
        return UserResponse(
            id=record["id"],
            username=record["username"],
            full_name=record["full_name"],
            email=record.get("email"),
            role=record["role"],
            university_id=record.get("university_id"),
            status=record.get("status", "ACTIVE"),
            created_at=record["created_at"].isoformat(),
        )
