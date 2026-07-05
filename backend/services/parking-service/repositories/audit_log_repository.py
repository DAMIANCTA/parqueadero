import uuid


class AuditLogRepository:
    def create_entry_audit_log(
        self,
        university_id: str,
        action: str,
        resource_id: str | None,
        metadata: dict,
    ) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "university_id": university_id,
            "action": action,
            "resource_id": resource_id,
            "metadata": metadata,
        }

    def create_exit_audit_log(
        self,
        university_id: str,
        action: str,
        resource_id: str | None,
        metadata: dict,
    ) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "university_id": university_id,
            "action": action,
            "resource_id": resource_id,
            "metadata": metadata,
        }
