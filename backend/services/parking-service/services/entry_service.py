import uuid

from config import settings
from repositories.access_event_repository import AccessEventRepository
from repositories.audit_log_repository import AuditLogRepository
from repositories.iot_repository import IoTRepository
from repositories.parking_session_repository import ParkingSessionRepository
from repositories.payment_repository import PaymentRepository
from repositories.plate_repository import PlateRepository
from repositories.vehicle_authorization_repository import VehicleAuthorizationRepository
from schemas.parking import FaceValidationResult, GateCommand, ParkingEntryRequest, ParkingEntryResponse, SessionData
from services.evidence_storage_service import EvidenceStorageService
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
        self.payment_repository = PaymentRepository()
        self.evidence_service = EvidenceStorageService()

    def process_entry(self, payload: ParkingEntryRequest) -> ParkingEntryResponse:
        face_mock_id = payload.face_mock_id or payload.face_image_id
        face_image_id = payload.face_image_id
        plate_image_id = payload.plate_image_id or payload.plate_evidence_id
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

        session_id = str(uuid.uuid4())
        face_validation = self.face_service.validate_entry_face(
            university_id=payload.university_id,
            session_id=session_id,
            face_image_id=face_image_id,
            confidence_face=payload.confidence_face,
            min_confidence=settings.min_face_confidence,
        )
        print(
            "parking-service entry_face_validation "
            f"session_id={session_id} image_id={face_image_id} "
            f"detected={face_validation.get('detected')} "
            f"provider={face_validation.get('provider')} "
            f"model_name={face_validation.get('model_name')} "
            f"bounding_box={face_validation.get('bounding_box')} "
            f"embedding_size={face_validation.get('embedding_size')} "
            f"warnings={face_validation.get('warnings')}"
        )
        if not face_validation["accepted"]:
            return self._reject(
                payload=payload,
                normalized_plate=normalized_plate,
                reason="Face detection failed",
                face_validation=face_validation,
            )

        registered_vehicle = self.vehicle_authorization_repository.detect_registered_vehicle(
            university_id=payload.university_id,
            plate_text=normalized_plate,
        )
        access_type = "VISITOR"
        person_type = "visitor"
        member_validation: dict | None = None
        session_person_id = None
        session_person_name = None
        session_role_type = None
        session_vehicle_id = None
        payment_status = "PENDING"

        if registered_vehicle["found"]:
            member_validation = self.vehicle_authorization_repository.validate_member_entry(
                university_id=payload.university_id,
                plate_text=normalized_plate,
                face_image_id=face_image_id,
                gate_id=payload.gate_id,
            )
            if not member_validation.get("authorized"):
                return self._reject(
                    payload=payload,
                    normalized_plate=normalized_plate,
                    reason=member_validation.get("message", "Member access validation failed"),
                    face_validation=face_validation,
                )
            access_type = "MEMBER"
            person_type = str(member_validation.get("role_type", "STAFF")).lower()
            if person_type == "staff":
                person_type = "employee"
            session_person_id = member_validation.get("person_id")
            session_person_name = member_validation.get("person_name")
            session_role_type = member_validation.get("role_type")
            session_vehicle_id = member_validation.get("vehicle_id")
            payment_status = "NOT_REQUIRED"

        session_record = self.parking_session_repository.create_entry_session(
            university_id=payload.university_id,
            campus_id=payload.campus_id,
            gate_id=payload.gate_id,
            plate_text=normalized_plate,
            person_type=person_type,
            entry_face_image_id=face_mock_id,
            access_type=access_type,
            payment_status=payment_status,
            person_id=session_person_id,
            person_name=session_person_name,
            role_type=session_role_type,
            vehicle_id=session_vehicle_id,
            entry_face_evidence_id=face_image_id,
            entry_plate_evidence_id=plate_image_id,
            session_id=session_id,
        )
        self.parking_session_repository.attach_evidence(
            session_record["session_id"],
            operation="entry",
            face_evidence_id=face_image_id,
            plate_evidence_id=plate_image_id,
        )
        self.evidence_service.link_evidence_to_session(face_image_id, session_record["session_id"], normalized_plate)
        self.evidence_service.link_evidence_to_session(plate_image_id, session_record["session_id"], normalized_plate)
        if access_type == "VISITOR":
            self.payment_repository.sync_visitor_session(
                session_id=session_record["session_id"],
                plate_text=normalized_plate,
            )
        else:
            self.payment_repository.sync_member_session(
                session_id=session_record["session_id"],
                plate_text=normalized_plate,
            )
        gate_command = self.iot_repository.open_gate(
            university_id=payload.university_id,
            campus_id=payload.campus_id,
            gate_id=payload.gate_id,
            plate_text=normalized_plate,
            session_id=session_record["session_id"],
            reason="entry_granted",
        )
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
                "person_type": person_type,
                "access_type": access_type,
                "person_id": session_person_id,
                "person_name": session_person_name,
                "role_type": session_role_type,
                "operator_username": payload.operator_username,
                "plate_detected_text": payload.plate_detected_text,
                "plate_detection_confidence": payload.plate_detection_confidence,
                "plate_override_reason": payload.plate_override_reason,
                "member_similarity": member_validation.get("similarity") if member_validation else None,
                "member_permit_status": member_validation.get("permit_status") if member_validation else None,
            },
        )

        return ParkingEntryResponse(
            authorized=True,
            status="AUTHORIZED",
            message="Vehicle entry authorized",
            session=SessionData(**session_record),
            gate_command=GateCommand(**gate_command),
            face_validation=FaceValidationResult(**face_validation),
            access_event_id=access_event["id"],
            audit_log_id=audit_log["id"],
        )

    def _reject(
        self,
        payload: ParkingEntryRequest,
        normalized_plate: str,
        reason: str,
        face_validation: dict | None = None,
    ) -> ParkingEntryResponse:
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
                "access_type": "VISITOR" if payload.person_type == "visitor" else "MEMBER_CANDIDATE",
                "reason": reason,
                "operator_username": payload.operator_username,
                "plate_detected_text": payload.plate_detected_text,
                "plate_detection_confidence": payload.plate_detection_confidence,
                "plate_override_reason": payload.plate_override_reason,
            },
        )
        gate_command = self.iot_repository.deny_gate(
            university_id=payload.university_id,
            campus_id=payload.campus_id,
            gate_id=payload.gate_id,
            plate_text=normalized_plate,
            session_id=None,
            reason=reason,
        )
        return ParkingEntryResponse(
            authorized=False,
            status="REJECTED",
            message=reason,
            session=None,
            gate_command=GateCommand(**gate_command),
            face_validation=FaceValidationResult(**face_validation) if face_validation else None,
            access_event_id=access_event["id"],
            audit_log_id=audit_log["id"],
        )
