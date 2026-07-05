import uuid


class IncidentRepository:
    def create_incident(
        self,
        university_id: str,
        gate_id: str,
        session_id: str | None,
        description: str,
    ) -> dict:
        return {
            "id": str(uuid.uuid4()),
            "university_id": university_id,
            "gate_id": gate_id,
            "session_id": session_id,
            "description": description,
            "incident_status": "open",
        }
