import uuid


class AccessEventRepository:
    def create_entry_event(
        self,
        university_id: str,
        gate_id: str,
        plate_text: str,
        session_id: str | None,
        result: str,
        reason: str,
    ) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "university_id": university_id,
            "gate_id": gate_id,
            "plate_text": plate_text,
            "session_id": session_id,
            "result": result,
            "reason": reason,
        }
