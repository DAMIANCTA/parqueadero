import httpx

from config import settings


class PaymentRepository:
    def sync_visitor_session(self, session_id: str, plate_text: str) -> dict | None:
        try:
            response = httpx.post(
                f"{settings.payment_service_url}/payments/internal/sessions/upsert",
                json={
                    "session_id": session_id,
                    "plate_text": plate_text,
                    "payment_status": "PENDING",
                },
                headers={"X-Internal-Audit-Key": settings.audit_internal_key},
                timeout=settings.payment_service_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def get_status_by_plate(self, plate_text: str) -> dict | None:
        try:
            response = httpx.get(
                f"{settings.payment_service_url}/payments/internal/status-by-plate",
                params={"plate": plate_text},
                headers={"X-Internal-Audit-Key": settings.audit_internal_key},
                timeout=settings.payment_service_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
