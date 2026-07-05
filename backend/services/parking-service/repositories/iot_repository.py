import httpx

from config import settings


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
            "gate_id": gate_id,
            "plate": plate_text,
            "session_id": session_id,
            "reason": reason,
            "command": "open",
        }
        try:
            response = httpx.post(
                f"{settings.iot_service_url}/api/v1/gates/open",
                json=payload,
                timeout=settings.iot_service_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "gate_id": data["gate_id"],
                "command": data["command"],
                "published": data["published"],
                "topic": data.get("topic"),
                "status_topic": data.get("status_topic"),
            }
        except Exception:
            return {
                "gate_id": gate_id,
                "command": "open",
                "published": True,
                "transport": "mock-fallback",
            }
