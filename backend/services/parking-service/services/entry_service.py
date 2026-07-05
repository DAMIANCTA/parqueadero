from config import settings
from repositories.access_event_repository import AccessEventRepository
from repositories.audit_log_repository import AuditLogRepository
from repositories.iot_repository import IoTRepository
from repositories.parking_session_repository import ParkingSessionRepository
from repositories.plate_repository import PlateRepository
from repositories.vehicle_authorization_repository import VehicleAuthorizationRepository
from schemas.parking import GateCommand, ParkingEntryRequest, ParkingEntryResponse, SessionData
from services.face_validation_service import FaceValidationService


class EntryService:
    def __init__(self) -> None:
        self.plate_repository = PlateRepository()
        self.face_service = FaceValidationService()
        self.vehicle_authorization_repository = VehicleAuthorizationRepository()
        self.parking_session_repository = ParkingSessionRepository()
        self.access_event_repository = AccessEventRepository()
        self.audit_log_repository = AuditLogRepository()
        self.iot_repository = IoTRepository()

    def process_entry(self, payload: ParkingEntryRequest) -> ParkingEntryResponse:
        try:
            normalized_plate = self.plate_repository.normalize_and_validate(
                plate_text=payload.plate_text,
                confidence_plate=payload.confidence_plate,
                min_confidence=settings.min_plate_confidence,
            )
        except ValueError as exc:
            return self._reject(
                payload=payload,
                normalized_plate=payload.plate_text.strip().upper().replace(" ", ""),
                reason=str(exc),
            )

        if payload.liveness_score < settings.min_liveness_score:
            return self._reject(
                payload=payload,
                normalized_plate=normalized_plate,
                reason="Liveness score too low",
            )

        face_validation = self.face_service.validate_entry_face(
            face_image_id=payload.face_image_id,
            confidence_face=payload.confidence_face,
            min_confidence=settings.min_face_confidence,
        )
        if not face_validation["accepted"]:
            return self._reject(
                payload=payload,
                normalized_plate=normalized_plate,
                reason="Face confidence too low",
            )

        if payload.person_type != "visitor":
            authorization = self.vehicle_authorization_repository.validate_plate_authorization(
                university_id=payload.university_id,
                plate_text=normalized_plate,
                person_type=payload.person_type,
            )
            if not authorization["authorized"]:
                return self._reject(
                    payload=payload,
                    normalized_plate=normalized_plate,
                    reason="Plate is not authorized for this person type",
                )

        session_record = self.parking_session_repository.create_entry_session(
            university_id=payload.university_id,
            campus_id=payload.campus_id,
            gate_id=payload.gate_id,
            plate_text=normalized_plate,
            person_type=payload.person_type,
        )
        gate_command = self.iot_repository.open_gate(gate_id=payload.gate_id, plate_text=normalized_plate)
        access_event = self.access_event_repository.create_entry_event(
            university_id=payload.university_id,
            gate_id=payload.gate_id,
            plate_text=normalized_plate,
            session_id=session_record["session_id"],
            result="success",
            reason="entry_granted",
        )
        audit_log = self.audit_log_repository.create_entry_audit_log(
            university_id=payload.university_id,
            action="parking.entry.authorized",
            resource_id=session_record["session_id"],
            metadata={
                "gate_id": payload.gate_id,
                "plate_text": normalized_plate,
                "person_type": payload.person_type,
            },
        )

        return ParkingEntryResponse(
            authorized=True,
            status="AUTHORIZED",
            message="Vehicle entry authorized",
            session=SessionData(**session_record),
            gate_command=GateCommand(**gate_command),
            access_event_id=access_event["id"],
            audit_log_id=audit_log["id"],
        )

    def _reject(self, payload: ParkingEntryRequest, normalized_plate: str, reason: str) -> ParkingEntryResponse:
        access_event = self.access_event_repository.create_entry_event(
            university_id=payload.university_id,
            gate_id=payload.gate_id,
            plate_text=normalized_plate,
            session_id=None,
            result="denied",
            reason=reason,
        )
        audit_log = self.audit_log_repository.create_entry_audit_log(
            university_id=payload.university_id,
            action="parking.entry.rejected",
            resource_id=None,
            metadata={
                "gate_id": payload.gate_id,
                "plate_text": normalized_plate,
                "person_type": payload.person_type,
                "reason": reason,
            },
        )
        return ParkingEntryResponse(
            authorized=False,
            status="REJECTED",
            message=reason,
            session=None,
            gate_command=None,
            access_event_id=access_event["id"],
            audit_log_id=audit_log["id"],
        )
