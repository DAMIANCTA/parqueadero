import uuid


class ParkingSessionRepository:
    active_visitor_sessions = {
        "VIS1234": {
            "session_id": "session-visitor-paid-001",
            "session_status": "INSIDE",
            "payment_status": "PAID",
            "person_type": "visitor",
            "plate_text": "VIS1234",
            "entry_face_image_id": "face-visitor-001",
        },
        "VISPEND": {
            "session_id": "session-visitor-pending-001",
            "session_status": "INSIDE",
            "payment_status": "PENDING",
            "person_type": "visitor",
            "plate_text": "VISPEND",
            "entry_face_image_id": "face-visitor-002",
        },
    }

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

    def find_active_session_by_plate(self, university_id: str, plate_text: str) -> dict | None:
        del university_id
        return self.active_visitor_sessions.get(plate_text)

    def close_session(self, session_id: str, plate_text: str, person_type: str, payment_status: str) -> dict:
        for session_plate, session in list(self.active_visitor_sessions.items()):
            if session["session_id"] == session_id:
                self.active_visitor_sessions.pop(session_plate, None)
                break
        return {
            "session_id": session_id,
            "session_status": "OUTSIDE",
            "payment_status": payment_status,
            "person_type": person_type,
            "plate_text": plate_text,
        }

    def create_registered_exit_record(self, plate_text: str, person_type: str) -> dict:
        return {
            "session_id": str(uuid.uuid4()),
            "session_status": "OUTSIDE",
            "payment_status": "NOT_REQUIRED",
            "person_type": person_type,
            "plate_text": plate_text,
        }
