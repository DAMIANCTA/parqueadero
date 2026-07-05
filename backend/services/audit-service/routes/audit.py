from fastapi import APIRouter, Query, Request

from config import settings
from schemas.audit import AuditEventRequest, AuditEventResponse, AuditLogListResponse
from security import require_permissions, verify_internal_audit_key
from services.audit_service import AuditService


router = APIRouter(prefix="/audit", tags=["audit"])
audit_service = AuditService()


@router.post("/logs/internal", response_model=AuditEventResponse)
def create_internal_log(payload: AuditEventRequest, request: Request) -> AuditEventResponse:
    verify_internal_audit_key(request, settings.audit_internal_key)
    record = audit_service.create_event(payload)
    return AuditEventResponse(accepted=True, event_id=record["id"])


@router.get("/logs", response_model=AuditLogListResponse, dependencies=[require_permissions("audit.read")])
def list_logs(limit: int = Query(default=50, ge=1, le=500)) -> AuditLogListResponse:
    items = audit_service.list_events(limit)
    return AuditLogListResponse(total=len(items), items=items)
