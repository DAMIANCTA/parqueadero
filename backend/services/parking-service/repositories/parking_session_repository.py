import uuid


class ParkingSessionRepository:
    def create_entry_session(
        self,
        university_id: str,
        campus_id: str,
        gate_id: str,
        plate_text: str,
        person_type: str,
    ) -> dict:
        del university_id, campus_id, gate_id
        return {
            "session_id": str(uuid.uuid4()),
            "session_status": "INSIDE",
            "payment_status": "PENDING" if person_type == "visitor" else "NOT_REQUIRED",
            "person_type": person_type,
            "plate_text": plate_text,
        }
