from datetime import datetime, UTC

import httpx

from config import settings


class PaymentRepository:
    def sync_session(self, session_id: str, plate_text: str, payment_status: str) -> dict | None:
        try:
            response = httpx.post(
                f"{settings.payment_service_url}/payments/internal/sessions/upsert",
                json={
                    "session_id": session_id,
                    "plate_text": plate_text,
                    "payment_status": payment_status,
                },
                headers={"X-Internal-Audit-Key": settings.audit_internal_key},
                timeout=settings.payment_service_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def sync_visitor_session(self, session_id: str, plate_text: str) -> dict | None:
        return self.sync_session(session_id=session_id, plate_text=plate_text, payment_status="PENDING")

    def sync_member_session(self, session_id: str, plate_text: str) -> dict | None:
        return self.sync_session(session_id=session_id, plate_text=plate_text, payment_status="NOT_REQUIRED")

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

    def close_visitor_session(self, session_id: str, plate_text: str, payment_status: str, exit_time: datetime | None = None) -> dict | None:
        try:
            response = httpx.post(
                f"{settings.payment_service_url}/payments/internal/sessions/close",
                json={
                    "session_id": session_id,
                    "plate_text": plate_text,
                    "payment_status": payment_status,
                    "exit_time": (exit_time or datetime.now(UTC)).isoformat(),
                    "session_status": "OUTSIDE",
                },
                headers={"X-Internal-Audit-Key": settings.audit_internal_key},
                timeout=settings.payment_service_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
