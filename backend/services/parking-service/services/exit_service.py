from datetime import datetime, UTC

from config import settings
from repositories.access_event_repository import AccessEventRepository
from repositories.audit_log_repository import AuditLogRepository
from repositories.incident_repository import IncidentRepository
from repositories.iot_repository import IoTRepository
from repositories.parking_session_repository import ParkingSessionRepository
from repositories.payment_repository import PaymentRepository
from repositories.plate_repository import PlateRepository
from repositories.vehicle_authorization_repository import VehicleAuthorizationRepository
from schemas.parking import GateCommand, ParkingExitRequest, ParkingExitResponse, SessionData
from services.evidence_storage_service import EvidenceStorageService
from services.face_validation_service import FaceValidationService


class ExitService:
    def __init__(self) -> None:
        self.plate_repository = PlateRepository()
        self.face_service = FaceValidationService()
        self.vehicle_authorization_repository = VehicleAuthorizationRepository()
        self.parking_session_repository = ParkingSessionRepository()
        self.access_event_repository = AccessEventRepository()
        self.audit_log_repository = AuditLogRepository()
        self.incident_repository = IncidentRepository()
        self.iot_repository = IoTRepository()
        self.payment_repository = PaymentRepository()
        self.evidence_service = EvidenceStorageService()

    def process_exit(self, payload: ParkingExitRequest) -> ParkingExitResponse:
        face_mock_id = payload.face_mock_id or payload.face_image_id
        payload.face_mock_id = face_mock_id
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
                create_incident=True,
            )

        if payload.liveness_score < settings.min_liveness_score:
            return self._reject(
                payload=payload,
                normalized_plate=normalized_plate,
                reason="Liveness score too low",
                create_incident=True,
            )

        visitor_session = self.parking_session_repository.find_active_session_by_plate(
            university_id=payload.university_id,
            plate_text=normalized_plate,
        )
        if visitor_session is not None and visitor_session["person_type"] == "visitor":
            return self._process_visitor_exit(payload, normalized_plate, visitor_session)

        return self._process_registered_exit(payload, normalized_plate)

    def _process_visitor_exit(
        self,
        payload: ParkingExitRequest,
        normalized_plate: str,
        visitor_session: dict,
    ) -> ParkingExitResponse:
        face_match = self.face_service.compare_entry_and_exit_faces(
            entry_face_image_id=visitor_session["entry_face_image_id"],
            exit_face_image_id=payload.face_mock_id or payload.face_image_id,
            confidence_face=payload.confidence_face,
            min_confidence=settings.min_face_confidence,
        )
        if not face_match["accepted"]:
            return self._reject(
                payload=payload,
                normalized_plate=normalized_plate,
                reason="Face does not match entry record",
                session_id=visitor_session["session_id"],
                create_incident=True,
            )

        payment_status = self.payment_repository.get_status_by_plate(normalized_plate)
        effective_payment_status = payment_status["payment_status"] if payment_status and payment_status.get("found") else visitor_session["payment_status"]
        payment_valid_until = None
        if payment_status and payment_status.get("found") and payment_status.get("payment_valid_until"):
            payment_valid_until = datetime.fromisoformat(str(payment_status["payment_valid_until"]).replace("Z", "+00:00"))
        print(
            "parking-service visitor_exit_payment_check "
            f"session_id={visitor_session['session_id']} plate_text={normalized_plate} "
            f"payment_status_before={visitor_session.get('payment_status')} "
            f"payment_status_effective={effective_payment_status} "
            f"paid_at={payment_status.get('paid_at') if payment_status else None} "
            f"paid_amount={payment_status.get('paid_amount') if payment_status else None} "
            f"payment_valid_until={payment_status.get('payment_valid_until') if payment_status else None} "
            f"session_status_before={visitor_session.get('session_status')}"
        )
        if effective_payment_status != "PAID":
            return self._reject(
                payload=payload,
                normalized_plate=normalized_plate,
                reason="Payment status is not PAID",
                session_id=visitor_session["session_id"],
                create_incident=True,
                publish_status=True,
                event_type="exit",
                status_reason="payment_pending",
                extra_metadata={
                    "payment_status_before": visitor_session.get("payment_status"),
                    "payment_status_after": effective_payment_status,
                    "paid_at": payment_status.get("paid_at") if payment_status else None,
                    "paid_amount": payment_status.get("paid_amount") if payment_status else None,
                    "payment_valid_until": payment_status.get("payment_valid_until") if payment_status else None,
                    "session_status_before": visitor_session.get("session_status"),
                },
            )
        if payment_valid_until is not None and datetime.now(UTC) > payment_valid_until:
            return self._reject(
                payload=payload,
                normalized_plate=normalized_plate,
                reason="Payment grace period expired",
                session_id=visitor_session["session_id"],
                create_incident=True,
                publish_status=True,
                event_type="exit",
                status_reason="payment_grace_expired",
                extra_metadata={
                    "payment_status_before": visitor_session.get("payment_status"),
                    "payment_status_after": effective_payment_status,
                    "paid_at": payment_status.get("paid_at") if payment_status else None,
                    "paid_amount": payment_status.get("paid_amount") if payment_status else None,
                    "payment_valid_until": payment_status.get("payment_valid_until") if payment_status else None,
                    "session_status_before": visitor_session.get("session_status"),
                },
            )

        session_record = self.parking_session_repository.close_session(
            session_id=visitor_session["session_id"],
            plate_text=normalized_plate,
            person_type="visitor",
            payment_status=effective_payment_status,
            exit_face_evidence_id=payload.face_image_id if payload.face_mock_id else payload.face_evidence_id,
            exit_plate_evidence_id=payload.plate_image_id or payload.plate_evidence_id,
        )
        self.payment_repository.close_visitor_session(
            session_id=visitor_session["session_id"],
            plate_text=normalized_plate,
            payment_status=effective_payment_status,
            exit_time=session_record.get("exit_time"),
        )
        self.evidence_service.link_evidence_to_session(
            payload.face_image_id if payload.face_mock_id else payload.face_evidence_id,
            session_record["session_id"],
            normalized_plate,
        )
        self.evidence_service.link_evidence_to_session(
            payload.plate_image_id or payload.plate_evidence_id,
            session_record["session_id"],
            normalized_plate,
        )
        return self._authorize_exit(
            payload=payload,
            normalized_plate=normalized_plate,
            session_record=session_record,
            action="parking.exit.authorized.visitor",
            event_reason="exit_granted",
            extra_metadata={
                "payment_status_before": visitor_session.get("payment_status"),
                "payment_status_after": effective_payment_status,
                "payment_valid_until": payment_status.get("payment_valid_until") if payment_status else None,
                "paid_at": payment_status.get("paid_at") if payment_status else None,
                "paid_amount": payment_status.get("paid_amount") if payment_status else None,
                "session_status_before": visitor_session.get("session_status"),
                "session_status_after": session_record.get("session_status"),
                "exit_time": session_record.get("exit_time").isoformat() if session_record.get("exit_time") else None,
            },
        )

    def _process_registered_exit(self, payload: ParkingExitRequest, normalized_plate: str) -> ParkingExitResponse:
        authorization = self.vehicle_authorization_repository.validate_registered_exit(
            university_id=payload.university_id,
            plate_text=normalized_plate,
            face_image_id=payload.face_mock_id or payload.face_image_id,
        )
        if not authorization["plate_exists"]:
            return self._reject(
                payload=payload,
                normalized_plate=normalized_plate,
                reason="Plate does not exist",
            )
        if not authorization["face_authorized"]:
            return self._reject(
                payload=payload,
                normalized_plate=normalized_plate,
                reason="Face does not belong to an authorized person for this plate",
            )
        if not authorization["permission_valid"]:
            return self._reject(
                payload=payload,
                normalized_plate=normalized_plate,
                reason="Permission is not valid",
            )

        face_match = self.face_service.validate_registered_face(
            face_image_id=payload.face_mock_id or payload.face_image_id,
            confidence_face=payload.confidence_face,
            min_confidence=settings.min_face_confidence,
        )
        if not face_match["accepted"]:
            return self._reject(
                payload=payload,
                normalized_plate=normalized_plate,
                reason="Face confidence too low",
            )

        session_record = self.parking_session_repository.create_registered_exit_record(
            plate_text=normalized_plate,
            person_type=authorization["person_type"],
            exit_face_evidence_id=payload.face_image_id if payload.face_mock_id else payload.face_evidence_id,
            exit_plate_evidence_id=payload.plate_image_id or payload.plate_evidence_id,
        )
        self.evidence_service.link_evidence_to_session(
            payload.face_image_id if payload.face_mock_id else payload.face_evidence_id,
            session_record["session_id"],
            normalized_plate,
        )
        self.evidence_service.link_evidence_to_session(
            payload.plate_image_id or payload.plate_evidence_id,
            session_record["session_id"],
            normalized_plate,
        )
        return self._authorize_exit(
            payload=payload,
            normalized_plate=normalized_plate,
            session_record=session_record,
            action="parking.exit.authorized.registered",
            event_reason="exit_granted",
        )

    def _authorize_exit(
        self,
        payload: ParkingExitRequest,
        normalized_plate: str,
        session_record: dict,
        action: str,
        event_reason: str,
        extra_metadata: dict | None = None,
    ) -> ParkingExitResponse:
        gate_command = self.iot_repository.open_gate(
            university_id=payload.university_id,
            campus_id=payload.campus_id,
            gate_id=payload.gate_id,
            plate_text=normalized_plate,
            session_id=session_record["session_id"],
            reason="exit_granted",
        )
        access_event = self.access_event_repository.create_exit_event(
            university_id=payload.university_id,
            gate_id=payload.gate_id,
            plate_text=normalized_plate,
            session_id=session_record["session_id"],
            result="success",
            reason=event_reason,
        )
        audit_log = self.audit_log_repository.create_exit_audit_log(
            university_id=payload.university_id,
            action=action,
            resource_id=session_record["session_id"],
            metadata={
                "gate_id": payload.gate_id,
                "plate_text": normalized_plate,
                "campus_id": payload.campus_id,
                "operator_username": payload.operator_username,
                "plate_detected_text": payload.plate_detected_text,
                "plate_detection_confidence": payload.plate_detection_confidence,
                "plate_override_reason": payload.plate_override_reason,
                **(extra_metadata or {}),
            },
        )
        print(
            "parking-service exit_authorized "
            f"session_id={session_record['session_id']} plate_text={normalized_plate} "
            f"payment_status_after={session_record.get('payment_status')} "
            f"session_status_after={session_record.get('session_status')} "
            f"exit_time={session_record.get('exit_time')}"
        )
        return ParkingExitResponse(
            authorized=True,
            status="AUTHORIZED",
            message="Vehicle exit authorized",
            session=SessionData(**session_record),
            gate_command=GateCommand(**gate_command),
            access_event_id=access_event["id"],
            audit_log_id=audit_log["id"],
            incident_id=None,
        )

    def _reject(
        self,
        payload: ParkingExitRequest,
        normalized_plate: str,
        reason: str,
        session_id: str | None = None,
        create_incident: bool = False,
        publish_status: bool = False,
        event_type: str = "exit",
        status_reason: str | None = None,
        extra_metadata: dict | None = None,
    ) -> ParkingExitResponse:
        access_event = self.access_event_repository.create_exit_event(
            university_id=payload.university_id,
            gate_id=payload.gate_id,
            plate_text=normalized_plate,
            session_id=session_id,
            result="denied",
            reason=reason,
        )
        audit_log = self.audit_log_repository.create_exit_audit_log(
            university_id=payload.university_id,
            action="parking.exit.rejected",
            resource_id=session_id,
            metadata={
                "gate_id": payload.gate_id,
                "plate_text": normalized_plate,
                "campus_id": payload.campus_id,
                "reason": reason,
                "operator_username": payload.operator_username,
                "plate_detected_text": payload.plate_detected_text,
                "plate_detection_confidence": payload.plate_detection_confidence,
                "plate_override_reason": payload.plate_override_reason,
                **(extra_metadata or {}),
            },
        )
        incident_id = None
        if create_incident:
            incident = self.incident_repository.create_incident(
                university_id=payload.university_id,
                gate_id=payload.gate_id,
                session_id=session_id,
                description=reason,
            )
            incident_id = incident["id"]

        if publish_status:
            self.iot_repository.report_gate_status(
                university_id=payload.university_id,
                campus_id=payload.campus_id,
                gate_id=payload.gate_id,
                plate_text=normalized_plate,
                barrier="closed",
                reason=status_reason or reason,
                event_type=event_type,
                access_status="rejected",
            )

        return ParkingExitResponse(
            authorized=False,
            status="REJECTED",
            message=reason,
            session=None,
            gate_command=None,
            access_event_id=access_event["id"],
            audit_log_id=audit_log["id"],
            incident_id=incident_id,
        )
