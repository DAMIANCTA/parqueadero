from repositories.audit_repository import AuditRepository
from schemas.audit import AuditEventRequest


class AuditService:
    def create_event(self, payload: AuditEventRequest) -> dict:
        return AuditRepository.add_event(payload.model_dump())

    def list_events(self, limit: int) -> list[dict]:
        return AuditRepository.list_events(limit)
