import socket
import uuid
from dataclasses import dataclass

import httpx
from psycopg import connect

from config import settings
from schemas.integration import (
    ChangePasswordRequest,
    DriverRegisterRequest,
    FaceEnrollMemberRequest,
    FaceProfileListResponse,
    CashierPaymentRegistrationRequest,
    DemoOpenGateRequest,
    LoginRequest,
    MemberAccessValidationRequest,
    MemberCreateRequest,
    MyVehicleCreateRequest,
    MyVehicleUpdateRequest,
    ParkingEntryRequest,
    ParkingExitRequest,
    MonthlyPermitCreateRequest,
    PaymentByPlateRequest,
    PlateDetectBatchRequest,
    PlateDetectRequest,
    UniversityCreateRequest,
    UserCreateRequest,
    VehicleAuthorizationRequest,
    VehicleCreateRequest,
)
from schemas.system import DependencyHealth


class FaceNotDetectedError(Exception):
    pass


class NoVehicleRegisteredError(Exception):
    pass
from security import encode_access_token


@dataclass
class DownstreamTarget:
    name: str
    base_url: str


class IntegrationService:
    def __init__(self) -> None:
        self.http_timeout = 2.0
        self.default_downstream_timeout = settings.downstream_default_timeout_seconds
        self.plate_downstream_timeout = settings.downstream_plate_timeout_seconds
        self.evidence_downstream_timeout = settings.downstream_evidence_timeout_seconds
        self.targets = {
            "auth": DownstreamTarget(name="auth-service", base_url=settings.auth_service_url.rstrip("/")),
            "vehicle": DownstreamTarget(name="vehicle-service", base_url=settings.vehicle_service_url.rstrip("/")),
            "parking": DownstreamTarget(name="parking-service", base_url=settings.parking_service_url.rstrip("/")),
            "face": DownstreamTarget(name="face-service", base_url=settings.face_service_url.rstrip("/")),
            "plate": DownstreamTarget(name="plate-service", base_url=settings.plate_service_url.rstrip("/")),
            "payment": DownstreamTarget(name="payment-service", base_url=settings.payment_service_url.rstrip("/")),
            "iot": DownstreamTarget(name="iot-service", base_url=settings.iot_service_url.rstrip("/")),
        }

    def collect_health(self) -> list[DependencyHealth]:
        return [
            self._check_http_service("parking-service", settings.parking_service_url),
            self._check_http_service("face-service", settings.face_service_url),
            self._check_http_service("plate-service", settings.plate_service_url),
            self._check_http_service("payment-service", settings.payment_service_url),
            self._check_http_service("iot-service", settings.iot_service_url),
            self._check_postgres(
                name="postgres-core",
                host=settings.postgres_core_host,
                port=settings.postgres_core_internal_port,
                dbname=settings.postgres_core_db,
                user=settings.postgres_core_user,
                password=settings.postgres_core_password,
            ),
            self._check_postgres(
                name="postgres-biometrics",
                host=settings.postgres_biometrics_host,
                port=settings.postgres_biometrics_internal_port,
                dbname=settings.postgres_biometrics_db,
                user=settings.postgres_biometrics_user,
                password=settings.postgres_biometrics_password,
            ),
            self._check_minio(),
            self._check_mqtt(),
        ]

    def proxy_entry(self, payload: ParkingEntryRequest) -> dict:
        return self._post_json(
            self.targets["parking"],
            "/parking/entry",
            payload.model_dump(),
            permissions=["parking.entry"],
        )

    def proxy_exit(self, payload: ParkingExitRequest) -> dict:
        return self._post_json(
            self.targets["parking"],
            "/parking/exit",
            payload.model_dump(),
            permissions=["parking.exit"],
        )

    def issue_token(self, payload: LoginRequest) -> dict:
        return self._post_json_without_token(
            self.targets["auth"],
            "/auth/token",
            payload.model_dump(),
        )

    def issue_login(self, payload: LoginRequest) -> dict:
        return self._post_json_without_token(
            self.targets["auth"],
            "/auth/login",
            payload.model_dump(),
        )

    def get_current_user(self, bearer_token: str) -> dict:
        return self._get_json_with_passthrough_token(
            self.targets["auth"],
            "/auth/me",
            bearer_token,
        )

    def change_password(self, bearer_token: str, payload: ChangePasswordRequest) -> dict:
        return self._post_json_with_passthrough_token(
            self.targets["auth"],
            "/auth/change-password",
            payload.model_dump(),
            bearer_token,
        )

    def list_universities(self, bearer_token: str) -> dict:
        return self._get_json_with_passthrough_token(
            self.targets["auth"],
            "/universities",
            bearer_token,
        )

    def create_university(self, payload: UniversityCreateRequest, bearer_token: str) -> dict:
        return self._post_json_with_passthrough_token(
            self.targets["auth"],
            "/universities",
            payload.model_dump(),
            bearer_token,
        )

    def list_users(self, bearer_token: str, university_id: str | None = None, role: str | None = None) -> dict:
        query_parts = []
        if university_id:
            query_parts.append(f"university_id={university_id}")
        if role:
            query_parts.append(f"role={role}")
        suffix = f"?{'&'.join(query_parts)}" if query_parts else ""
        return self._get_json_with_passthrough_token(
            self.targets["auth"],
            f"/users{suffix}",
            bearer_token,
        )

    def create_user(self, payload: UserCreateRequest, bearer_token: str) -> dict:
        return self._post_json_with_passthrough_token(
            self.targets["auth"],
            "/users",
            payload.model_dump(),
            bearer_token,
        )

    def open_demo_gate(self, payload: DemoOpenGateRequest) -> dict:
        demo_event_id = f"demo-{uuid.uuid4()}"
        downstream = self.open_iot_gate(
            payload.gate_id,
            {
                "university_id": payload.university_id,
                "campus_id": payload.campus_id,
                "plate": payload.plate,
                "session_id": demo_event_id,
                "reason": "demo_validated",
            },
        )
        return {
            "status": "OPEN_COMMAND_SENT",
            "message": "La barrera demo fue enviada a abrir.",
            "demo_event_id": demo_event_id,
            "topic": downstream["topic"],
            "status_topic": downstream["event_topic"],
            "command": downstream["command"],
            "published": downstream["published"],
            "payload": {
                "command": downstream["command"],
                "command_code": downstream["command_code"],
                "plate": payload.plate,
                "session_id": demo_event_id,
                "reason": "demo_validated",
            },
        }

    def pay_session_by_plate(self, payload: PaymentByPlateRequest) -> dict:
        return self._post_json(
            self.targets["payment"],
            "/payments/pay-by-plate",
            payload.model_dump(),
            permissions=["payments.pay"],
        )

    def get_payment_by_plate(self, plate_text: str, university_id: str | None = None) -> dict:
        suffix = f"?university_id={university_id}" if university_id else ""
        return self._get_json(
            self.targets["payment"],
            f"/payments/by-plate/{plate_text}{suffix}",
            permissions=["payments.read"],
        )

    def register_cash_payment(self, payload: CashierPaymentRegistrationRequest) -> dict:
        return self._post_json(
            self.targets["payment"],
            "/payments/register-cash-payment",
            payload.model_dump(),
            permissions=["payments.pay"],
        )

    def open_iot_gate(self, gate_id: str, payload: dict) -> dict:
        return self._post_json(
            self.targets["iot"],
            f"/gates/{gate_id}/open",
            payload,
            permissions=["iot.gates.open"],
        )

    def deny_iot_gate(self, gate_id: str, payload: dict) -> dict:
        return self._post_json(
            self.targets["iot"],
            f"/gates/{gate_id}/deny",
            payload,
            permissions=["iot.gates.deny"],
        )

    def get_iot_gate_status(self, gate_id: str) -> dict:
        return self._get_json(
            self.targets["iot"],
            f"/gates/{gate_id}/status",
            permissions=["iot.gates.read"],
        )

    def get_admin_dashboard_summary(self, university_id: str | None = None) -> dict:
        summary = self._get_json(
            self.targets["payment"],
            f"/payments/admin/dashboard-summary{f'?university_id={university_id}' if university_id else ''}",
            permissions=["payments.read"],
        )
        audit_events = self.get_admin_audit_events(limit=200)
        summary["rejected_exits_today"] = self._count_rejected_exits(audit_events.get("items", []))
        return summary

    def get_admin_active_sessions(self, university_id: str | None = None) -> dict:
        return self._get_json(
            self.targets["payment"],
            f"/payments/admin/active-sessions{f'?university_id={university_id}' if university_id else ''}",
            permissions=["payments.read"],
        )

    def get_admin_session_history(self, university_id: str | None = None) -> dict:
        return self._get_json(
            self.targets["payment"],
            f"/payments/admin/session-history{f'?university_id={university_id}' if university_id else ''}",
            permissions=["payments.read"],
        )

    def get_admin_audit_events(self, *, limit: int = 50) -> dict:
        return self._get_json(
            DownstreamTarget(name="audit-service", base_url=settings.audit_service_url.rstrip("/")),
            f"/audit/logs?limit={limit}",
            permissions=["audit.read"],
        )

    def get_face_config(self) -> dict:
        return self._get_json(
            self.targets["face"],
            "/faces/config",
            permissions=["faces.verify"],
        )

    def create_member(self, payload: MemberCreateRequest) -> dict:
        return self._post_json(self.targets["vehicle"], "/members", payload.model_dump(), permissions=["members.write"])

    def list_members(self, university_id: str | None = None) -> dict:
        suffix = f"?university_id={university_id}" if university_id else ""
        return self._get_json(self.targets["vehicle"], f"/members{suffix}", permissions=["members.read"])

    def get_member(self, member_id: str) -> dict:
        return self._get_json(self.targets["vehicle"], f"/members/{member_id}", permissions=["members.read"])

    def create_vehicle(self, payload: VehicleCreateRequest) -> dict:
        return self._post_json(self.targets["vehicle"], "/vehicles", payload.model_dump(), permissions=["vehicles.write"])

    def list_vehicles(self, university_id: str | None = None) -> dict:
        suffix = f"?university_id={university_id}" if university_id else ""
        return self._get_json(self.targets["vehicle"], f"/vehicles{suffix}", permissions=["vehicles.read"])

    def register_driver(self, payload: DriverRegisterRequest) -> dict:
        return self._post_json_without_token(self.targets["auth"], "/auth/register", payload.model_dump())

    def list_my_vehicles(self, user_id: str) -> dict:
        return self._get_json(
            self.targets["vehicle"],
            f"/members/by-user/{user_id}/vehicles",
            permissions=["members.read", "vehicles.read"],
        )

    def register_my_vehicle(self, user: dict, payload: MyVehicleCreateRequest, university_id: str) -> dict:
        body = {
            "user_id": user["sub"],
            "full_name": user.get("full_name") or user["username"],
            "document_number": None,
            "phone": None,
            "university_id": university_id,
            **payload.model_dump(),
        }
        return self._post_json(
            self.targets["vehicle"],
            "/vehicles/register-owned",
            body,
            permissions=["vehicles.write", "members.write"],
        )

    def update_my_vehicle(self, user_id: str, payload: MyVehicleUpdateRequest) -> dict:
        vehicles = self.list_my_vehicles(user_id)
        if not vehicles["items"]:
            raise NoVehicleRegisteredError("No tienes un vehículo registrado")
        vehicle_id = vehicles["items"][0]["id"]
        return self._patch_json(
            self.targets["vehicle"],
            f"/vehicles/{vehicle_id}",
            payload.model_dump(exclude_none=True),
            permissions=["vehicles.write"],
        )

    def get_my_active_session(self, plate_text: str) -> dict:
        return self._get_json(
            self.targets["parking"],
            f"/parking/active-session/{plate_text}",
            permissions=["parking.entry"],
        )

    def get_my_history(self, plate_text: str, limit: int = 100) -> dict:
        return self._get_json(
            self.targets["parking"],
            f"/parking/history?plate_text={plate_text}&limit={limit}",
            permissions=["parking.entry"],
        )

    def get_member_by_user(self, user_id: str) -> dict:
        return self._get_json(self.targets["vehicle"], f"/members/by-user/{user_id}", permissions=["members.read"])

    def check_face_live(self, *, file_bytes: bytes, filename: str, content_type: str) -> dict:
        token = self._build_internal_token(["faces.verify"])
        files = {"file": (filename, file_bytes, content_type or "image/jpeg")}
        with httpx.Client(timeout=self._build_timeout(5.0)) as client:
            response = client.post(
                f"{self.targets['face'].base_url}/faces/detect-live",
                files=files,
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
        return response.json()

    def detect_face(self, image_id: str, university_id: str) -> dict:
        return self._post_json(
            self.targets["face"],
            "/faces/detect",
            {"image_id": image_id, "university_id": university_id},
            permissions=["faces.verify"],
        )

    def enroll_my_face(
        self,
        user: dict,
        plate_text: str,
        *,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> dict:
        member = self.get_member_by_user(user["sub"])
        university_id = user.get("university_id") or ""
        evidence = self.proxy_evidence_upload(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
            image_type="face_enrollment",
            plate=plate_text,
            university_id=university_id,
            session_id=None,
        )
        # Reutiliza el mismo servicio de deteccion facial que usa garita para
        # rechazar fotos sin un rostro valido/de buena calidad antes de
        # enrolarlas (en vez de confiar ciegamente en la foto subida).
        detection = self.detect_face(evidence["image_id"], university_id)
        if not detection.get("detected"):
            raise FaceNotDetectedError(
                "No se detectó un rostro válido en la foto. Intenta de nuevo con buena iluminación y mirando a la cámara."
            )
        payload = FaceEnrollMemberRequest(face_image_id=evidence["image_id"])
        return self.enroll_member_face(member["id"], payload)

    def get_vehicle_by_plate(self, plate_text: str) -> dict:
        return self._get_json(self.targets["vehicle"], f"/vehicles/by-plate/{plate_text}", permissions=["vehicles.read"])

    def enroll_member_face(self, member_id: str, payload: FaceEnrollMemberRequest) -> dict:
        return self._post_json(
            self.targets["vehicle"],
            f"/members/{member_id}/faces/enroll",
            payload.model_dump(),
            permissions=["faces.enroll", "members.write"],
        )

    def list_face_profiles(self, university_id: str | None = None) -> dict:
        suffix = f"?university_id={university_id}" if university_id else ""
        return self._get_json(self.targets["vehicle"], f"/members/faces{suffix}", permissions=["members.read"])

    def authorize_vehicle_person(self, vehicle_id: str, payload: VehicleAuthorizationRequest) -> dict:
        return self._post_json(
            self.targets["vehicle"],
            f"/vehicles/{vehicle_id}/authorize-person",
            payload.model_dump(),
            permissions=["vehicles.write", "members.write"],
        )

    def create_monthly_permit(self, payload: MonthlyPermitCreateRequest) -> dict:
        return self._post_json(self.targets["vehicle"], "/permits/monthly", payload.model_dump(mode="json"), permissions=["permits.write"])

    def list_monthly_permits(self, university_id: str | None = None) -> dict:
        suffix = f"?university_id={university_id}" if university_id else ""
        return self._get_json(self.targets["vehicle"], f"/permits/monthly{suffix}", permissions=["permits.read"])

    def get_permit_by_plate(self, plate_text: str) -> dict:
        return self._get_json(self.targets["vehicle"], f"/permits/by-plate/{plate_text}", permissions=["permits.read"])

    def validate_member_entry(self, payload: MemberAccessValidationRequest) -> dict:
        return self._post_json(
            self.targets["vehicle"],
            "/access/validate-member-entry",
            payload.model_dump(),
            permissions=["members.read"],
        )

    def proxy_plate_detection(self, payload: PlateDetectRequest) -> dict:
        return self._post_json(
            self.targets["plate"],
            "/plates/detect",
            payload.model_dump(),
            permissions=["plates.detect"],
            timeout_seconds=self.plate_downstream_timeout,
        )

    def proxy_plate_detection_batch(self, payload: PlateDetectBatchRequest) -> dict:
        return self._post_json(
            self.targets["plate"],
            "/plates/detect-batch",
            payload.model_dump(),
            permissions=["plates.detect"],
            timeout_seconds=self.plate_downstream_timeout,
        )

    def proxy_evidence_upload(
        self,
        *,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        image_type: str,
        plate: str,
        university_id: str | None = None,
        session_id: str | None,
    ) -> dict:
        token = self._build_internal_token(["parking.entry"])
        files = {
            "file": (
                filename,
                file_bytes,
                content_type or "application/octet-stream",
            )
        }
        data = {
            "image_type": image_type,
            "plate": plate,
        }
        if university_id:
            data["university_id"] = university_id
        if session_id:
            data["session_id"] = session_id
        with httpx.Client(timeout=self._build_timeout(self.evidence_downstream_timeout)) as client:
            response = client.post(
                f"{self.targets['parking'].base_url}/evidence/upload",
                data=data,
                files=files,
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
        return response.json()

    def get_parking_history(self, university_id: str | None = None) -> dict:
        return self._get_json(
            self.targets["parking"],
            f"/parking/history{f'?university_id={university_id}' if university_id else ''}",
            permissions=["parking.entry"],
        )

    def get_evidence_image_bytes(self, image_id: str) -> tuple[bytes, str]:
        token = self._build_internal_token(["parking.entry"])
        with httpx.Client(timeout=self._build_timeout(self.evidence_downstream_timeout)) as client:
            response = client.get(
                f"{self.targets['parking'].base_url}/evidence/image/{image_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "image/jpeg")

    def get_evidence_by_plate(self, plate_text: str, *, include_expired: bool = True) -> dict:
        return self._get_json(
            self.targets["parking"],
            f"/evidence/by-plate/{plate_text}?include_expired={str(include_expired).lower()}",
            permissions=["parking.entry"],
        )

    def _check_http_service(self, name: str, base_url: str) -> DependencyHealth:
        try:
            with httpx.Client(timeout=self.http_timeout) as client:
                response = client.get(f"{base_url.rstrip('/')}/health")
            if response.status_code == 200:
                return DependencyHealth(name=name, status="ok", detail="HTTP health responded with 200")
            return DependencyHealth(name=name, status="error", detail=f"HTTP health returned {response.status_code}")
        except httpx.HTTPError as exc:
            return DependencyHealth(name=name, status="error", detail=f"HTTP health failed: {exc}")

    def _check_postgres(
        self,
        *,
        name: str,
        host: str,
        port: int,
        dbname: str,
        user: str,
        password: str,
    ) -> DependencyHealth:
        try:
            connection = connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
                connect_timeout=2,
            )
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            connection.close()
            return DependencyHealth(name=name, status="ok", detail="Database connection and SELECT 1 succeeded")
        except Exception as exc:  # pragma: no cover - defensive runtime integration
            return DependencyHealth(name=name, status="error", detail=f"Database check failed: {exc}")

    def _check_minio(self) -> DependencyHealth:
        try:
            with httpx.Client(timeout=self.http_timeout) as client:
                response = client.get(f"{settings.minio_internal_url.rstrip('/')}/minio/health/live")
            if response.status_code == 200:
                return DependencyHealth(name="minio", status="ok", detail="MinIO live health responded with 200")
            return DependencyHealth(name="minio", status="error", detail=f"MinIO health returned {response.status_code}")
        except httpx.HTTPError as exc:
            return DependencyHealth(name="minio", status="error", detail=f"MinIO health failed: {exc}")

    def _check_mqtt(self) -> DependencyHealth:
        try:
            with socket.create_connection((settings.mqtt_host, settings.mqtt_port), timeout=2):
                pass
            return DependencyHealth(name="mqtt", status="ok", detail="TCP connection to broker succeeded")
        except OSError as exc:
            return DependencyHealth(name="mqtt", status="error", detail=f"MQTT connection failed: {exc}")

    def _post_json(
        self,
        target: DownstreamTarget,
        path: str,
        payload: dict,
        *,
        permissions: list[str],
        timeout_seconds: float | None = None,
    ) -> dict:
        token = self._build_internal_token(permissions)
        with httpx.Client(timeout=self._build_timeout(timeout_seconds or self.default_downstream_timeout)) as client:
            response = client.post(
                f"{target.base_url}{path}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
        response.raise_for_status()
        return response.json()

    def _patch_json(
        self,
        target: DownstreamTarget,
        path: str,
        payload: dict,
        *,
        permissions: list[str],
        timeout_seconds: float | None = None,
    ) -> dict:
        token = self._build_internal_token(permissions)
        with httpx.Client(timeout=self._build_timeout(timeout_seconds or self.default_downstream_timeout)) as client:
            response = client.patch(
                f"{target.base_url}{path}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
        response.raise_for_status()
        return response.json()

    def _post_json_without_token(self, target: DownstreamTarget, path: str, payload: dict) -> dict:
        with httpx.Client(timeout=self._build_timeout(self.default_downstream_timeout)) as client:
            response = client.post(
                f"{target.base_url}{path}",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        response.raise_for_status()
        return response.json()

    def _get_json(
        self,
        target: DownstreamTarget,
        path: str,
        *,
        permissions: list[str],
        timeout_seconds: float | None = None,
    ) -> dict:
        token = self._build_internal_token(permissions)
        with httpx.Client(timeout=self._build_timeout(timeout_seconds or self.default_downstream_timeout)) as client:
            response = client.get(
                f"{target.base_url}{path}",
                headers={"Authorization": f"Bearer {token}"},
            )
        response.raise_for_status()
        return response.json()

    def _get_json_with_passthrough_token(self, target: DownstreamTarget, path: str, bearer_token: str) -> dict:
        with httpx.Client(timeout=self._build_timeout(self.default_downstream_timeout)) as client:
            response = client.get(
                f"{target.base_url}{path}",
                headers={"Authorization": f"Bearer {bearer_token}"},
            )
        response.raise_for_status()
        return response.json()

    def _post_json_with_passthrough_token(
        self,
        target: DownstreamTarget,
        path: str,
        payload: dict,
        bearer_token: str,
    ) -> dict:
        with httpx.Client(timeout=self._build_timeout(self.default_downstream_timeout)) as client:
            response = client.post(
                f"{target.base_url}{path}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {bearer_token}",
                    "Content-Type": "application/json",
                },
            )
        response.raise_for_status()
        return response.json()

    def _build_timeout(self, seconds: float) -> httpx.Timeout:
        return httpx.Timeout(timeout=seconds, connect=min(seconds, 5.0))

    def _count_rejected_exits(self, audit_items: list[dict]) -> int:
        count = 0
        for item in audit_items:
            if item.get("path") != "/parking/exit":
                continue
            if int(item.get("status_code") or 0) >= 400:
                count += 1
        return count

    def _build_internal_token(self, permissions: list[str]) -> str:
        return encode_access_token(
            secret_key=settings.jwt_secret_key,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            expires_minutes=settings.jwt_access_token_expires_minutes,
            claims={
                "sub": "api-gateway",
                "username": "api-gateway",
                "roles": ["service_gateway"],
                "permissions": permissions + ["*"],
                "university_id": "system",
            },
        )
