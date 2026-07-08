import uuid
from datetime import datetime, UTC


class ParkingSessionRepository:
    active_sessions = {
        "VIS1234": {
            "session_id": "session-visitor-paid-001",
            "session_status": "INSIDE",
            "payment_status": "PAID",
            "person_type": "visitor",
            "plate_text": "VIS1234",
            "entry_face_image_id": "face-visitor-001",
            "entry_face_evidence_id": None,
            "entry_plate_evidence_id": None,
            "exit_face_evidence_id": None,
            "exit_plate_evidence_id": None,
            "exit_time": None,
        },
        "VISPEND": {
            "session_id": "session-visitor-pending-001",
            "session_status": "INSIDE",
            "payment_status": "PENDING",
            "person_type": "visitor",
            "plate_text": "VISPEND",
            "entry_face_image_id": "face-visitor-002",
            "entry_face_evidence_id": None,
            "entry_plate_evidence_id": None,
            "exit_face_evidence_id": None,
            "exit_plate_evidence_id": None,
            "exit_time": None,
        },
    }
    active_visitor_sessions = {
        plate: session.copy()
        for plate, session in active_sessions.items()
        if session["person_type"] == "visitor"
    }
    session_records = {
        session["session_id"]: session.copy()
        for session in active_sessions.values()
    }

    def create_entry_session(
        self,
        university_id: str,
        campus_id: str,
        gate_id: str,
        plate_text: str,
        person_type: str,
        entry_face_image_id: str,
        entry_face_evidence_id: str | None = None,
        entry_plate_evidence_id: str | None = None,
        session_id: str | None = None,
    ) -> dict:
        del university_id, campus_id, gate_id
        session = {
            "session_id": session_id or str(uuid.uuid4()),
            "session_status": "INSIDE",
            "payment_status": "PENDING" if person_type == "visitor" else "NOT_REQUIRED",
            "person_type": person_type,
            "plate_text": plate_text,
            "entry_face_image_id": entry_face_image_id,
            "entry_face_evidence_id": entry_face_evidence_id,
            "entry_plate_evidence_id": entry_plate_evidence_id,
            "exit_face_evidence_id": None,
            "exit_plate_evidence_id": None,
            "exit_time": None,
        }
        self.active_sessions[plate_text] = session.copy()
        if person_type == "visitor":
            self.active_visitor_sessions[plate_text] = session.copy()
        self.session_records[session["session_id"]] = session.copy()
        return self._session_summary(session)

    def find_active_session_by_plate(self, university_id: str, plate_text: str) -> dict | None:
        del university_id
        return self.active_sessions.get(plate_text)

    def close_session(
        self,
        session_id: str,
        plate_text: str,
        person_type: str,
        payment_status: str,
        exit_face_evidence_id: str | None = None,
        exit_plate_evidence_id: str | None = None,
    ) -> dict:
        record = self.session_records.get(session_id, {}).copy()
        exit_time = datetime.now(UTC)
        for session_plate, session in list(self.active_sessions.items()):
            if session["session_id"] == session_id:
                session["session_status"] = "OUTSIDE"
                session["payment_status"] = payment_status
                session["exit_face_evidence_id"] = exit_face_evidence_id
                session["exit_plate_evidence_id"] = exit_plate_evidence_id
                session["exit_time"] = exit_time
                record = session.copy()
                self.active_sessions.pop(session_plate, None)
                if session["person_type"] == "visitor":
                    self.active_visitor_sessions.pop(session_plate, None)
                break
        record.update(
            {
                "session_id": session_id,
                "session_status": "OUTSIDE",
                "payment_status": payment_status,
                "person_type": person_type,
                "plate_text": plate_text,
                "exit_face_evidence_id": exit_face_evidence_id,
                "exit_plate_evidence_id": exit_plate_evidence_id,
                "exit_time": exit_time,
            }
        )
        self.session_records[session_id] = record
        return self._session_summary(record)

    def create_registered_exit_record(
        self,
        plate_text: str,
        person_type: str,
        exit_face_evidence_id: str | None = None,
        exit_plate_evidence_id: str | None = None,
    ) -> dict:
        session = {
            "session_id": str(uuid.uuid4()),
            "session_status": "OUTSIDE",
            "payment_status": "NOT_REQUIRED",
            "person_type": person_type,
            "plate_text": plate_text,
            "entry_face_image_id": None,
            "entry_face_evidence_id": None,
            "entry_plate_evidence_id": None,
            "exit_face_evidence_id": exit_face_evidence_id,
            "exit_plate_evidence_id": exit_plate_evidence_id,
            "exit_time": datetime.now(UTC),
        }
        self.session_records[session["session_id"]] = session.copy()
        return self._session_summary(session)

    def attach_evidence(
        self,
        session_id: str,
        *,
        operation: str,
        face_evidence_id: str | None = None,
        plate_evidence_id: str | None = None,
    ) -> None:
        record = self.session_records.get(session_id)
        if record is None:
            return

        face_key = f"{operation}_face_evidence_id"
        plate_key = f"{operation}_plate_evidence_id"
        if face_evidence_id:
            record[face_key] = face_evidence_id
        if plate_evidence_id:
            record[plate_key] = plate_evidence_id
        self.session_records[session_id] = record

        for plate, session in self.active_sessions.items():
            if session["session_id"] == session_id:
                if face_evidence_id:
                    session[face_key] = face_evidence_id
                if plate_evidence_id:
                    session[plate_key] = plate_evidence_id
                self.active_sessions[plate] = session
                if session["person_type"] == "visitor":
                    self.active_visitor_sessions[plate] = session.copy()
                break

    def _session_summary(self, session: dict) -> dict:
        return {
            "session_id": session["session_id"],
            "session_status": session["session_status"],
            "payment_status": session["payment_status"],
            "person_type": session["person_type"],
            "plate_text": session["plate_text"],
            "exit_time": session.get("exit_time"),
        }
