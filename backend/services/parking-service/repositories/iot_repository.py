import httpx

from config import settings
from security import encode_access_token


class IoTRepository:
    def open_gate(
        self,
        university_id: str,
        campus_id: str,
        gate_id: str,
        plate_text: str,
        session_id: str,
        reason: str,
    ) -> dict:
        payload = {
            "university_id": university_id,
            "campus_id": campus_id,
            "plate": plate_text,
            "session_id": session_id,
            "reason": reason,
        }
        try:
            response = httpx.post(
                f"{settings.iot_service_url}/gates/{gate_id}/open",
                json=payload,
                headers=self._build_internal_headers(["iot.gates.open"]),
                timeout=settings.iot_service_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "gate_id": data["gate_id"],
                "command": data["command"],
                "published": data["published"],
                "topic": data.get("topic"),
                "status_topic": data.get("event_topic"),
            }
        except Exception:
            return {
                "gate_id": gate_id,
                "command": "open",
                "published": False,
                "transport": "mock-fallback",
            }

    def deny_gate(
        self,
        university_id: str,
        campus_id: str,
        gate_id: str,
        plate_text: str,
        session_id: str | None,
        reason: str,
    ) -> dict:
        payload = {
            "university_id": university_id,
            "campus_id": campus_id,
            "plate": plate_text,
            "session_id": session_id,
            "reason": reason,
        }
        try:
            response = httpx.post(
                f"{settings.iot_service_url}/gates/{gate_id}/deny",
                json=payload,
                headers=self._build_internal_headers(["iot.gates.deny"]),
                timeout=settings.iot_service_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "gate_id": data["gate_id"],
                "command": data["command"],
                "published": data["published"],
                "topic": data.get("topic"),
                "status_topic": data.get("event_topic"),
            }
        except Exception:
            return {
                "gate_id": gate_id,
                "command": "deny",
                "published": False,
                "transport": "mock-fallback",
            }

    def report_gate_status(
        self,
        university_id: str,
        campus_id: str,
        gate_id: str,
        plate_text: str,
        barrier: str,
        reason: str,
        event_type: str,
        access_status: str,
    ) -> dict:
        payload = {
            "university_id": university_id,
            "campus_id": campus_id,
            "gate_id": gate_id,
            "plate": plate_text,
            "barrier": barrier,
            "device_status": "online",
            "reason": reason,
            "event_type": event_type,
            "access_status": access_status,
        }
        try:
            response = httpx.post(
                f"{settings.iot_service_url}/api/v1/gates/status",
                json=payload,
                headers=self._build_internal_headers(["iot.gates.open"]),
                timeout=settings.iot_service_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return {
                "gate_id": gate_id,
                "published": False,
                "barrier": barrier,
                "reason": reason,
                "event_type": event_type,
                "access_status": access_status,
            }

    def _build_internal_headers(self, permissions: list[str]) -> dict[str, str]:
        token = encode_access_token(
            secret_key=settings.jwt_secret_key,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            expires_minutes=5,
            claims={
                "sub": "parking-service",
                "username": "parking-service",
                "roles": ["service_parking"],
                "permissions": permissions + ["*"],
                "university_id": "system",
            },
        )
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
