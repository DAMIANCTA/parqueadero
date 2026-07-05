import uuid


class AuditLogRepository:
    def create_payment_audit_log(self, action: str, resource_id: str, metadata: dict) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "action": action,
            "resource_id": resource_id,
            "metadata": metadata,
        }
