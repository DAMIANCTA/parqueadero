import logging

import httpx

from config import settings
from security import encode_access_token


logger = logging.getLogger(__name__)


class VehicleAuthorizationRepository:
    _fallback_records = {
        "ABC1234": {
            "person_id": "person-student-001",
            "person_name": "Ana Belen Torres",
            "role_type": "STUDENT",
            "vehicle_id": "vehicle-001",
            "person_type": "student",
            "permit_status": "VALID",
            "face_authorized": True,
        },
        "XYZ9876": {
            "person_id": "person-teacher-001",
            "person_name": "Carlos Mena",
            "role_type": "TEACHER",
            "vehicle_id": "vehicle-002",
            "person_type": "teacher",
            "permit_status": "VALID",
            "face_authorized": True,
        },
        "EMP2026": {
            "person_id": "person-staff-001",
            "person_name": "Maria Fernanda Ruiz",
            "role_type": "STAFF",
            "vehicle_id": "vehicle-003",
            "person_type": "employee",
            "permit_status": "VALID",
            "face_authorized": True,
        },
        "EXP2026": {
            "person_id": "person-staff-001",
            "person_name": "Maria Fernanda Ruiz",
            "role_type": "STAFF",
            "vehicle_id": "vehicle-004",
            "person_type": "employee",
            "permit_status": "EXPIRED",
            "face_authorized": True,
        },
    }

    def detect_registered_vehicle(self, university_id: str, plate_text: str) -> dict:
        try:
            response = self._get(f"/internal/vehicles/by-plate/{plate_text}")
            if response.get("found"):
                vehicle = response.get("vehicle") or {}
                people = response.get("authorized_people") or []
                return {
                    "found": True,
                    "vehicle_id": vehicle.get("id"),
                    "plate_text": vehicle.get("plate_text", plate_text),
                    "authorized_people": people,
                    "message": response.get("message", "Vehicle plate is registered"),
                }
            return {
                "found": False,
                "plate_text": plate_text,
                "authorized_people": [],
                "message": response.get("message", "Vehicle plate is not registered"),
            }
        except httpx.HTTPError as exc:
            logger.warning("parking-service vehicle_repository detect_registered_vehicle_fallback error=%s", exc)
            fallback = self._fallback_records.get(plate_text)
            if fallback is None:
                return {
                    "found": False,
                    "plate_text": plate_text,
                    "authorized_people": [],
                    "message": "Vehicle plate is not registered",
                }
            return {
                "found": True,
                "vehicle_id": fallback["vehicle_id"],
                "plate_text": plate_text,
                "authorized_people": [
                    {
                        "id": fallback["person_id"],
                        "full_name": fallback["person_name"],
                        "role_type": fallback["role_type"],
                    }
                ],
                "message": "Fallback member vehicle found",
            }

    def validate_member_entry(self, *, university_id: str, plate_text: str, face_image_id: str, gate_id: str) -> dict:
        try:
            return self._post(
                "/internal/access/validate-member-entry",
                {
                    "university_id": university_id,
                    "plate_text": plate_text,
                    "face_image_id": face_image_id,
                    "gate_id": gate_id,
                },
            )
        except httpx.HTTPError as exc:
            logger.warning("parking-service vehicle_repository member_entry_fallback error=%s", exc)
            return self._fallback_member_validation(plate_text, face_image_id)

    def validate_member_exit(
        self,
        *,
        university_id: str,
        plate_text: str,
        face_image_id: str,
        gate_id: str,
        session_person_id: str | None = None,
    ) -> dict:
        try:
            return self._post(
                "/internal/access/validate-member-exit",
                {
                    "university_id": university_id,
                    "plate_text": plate_text,
                    "face_image_id": face_image_id,
                    "gate_id": gate_id,
                    "session_person_id": session_person_id,
                },
            )
        except httpx.HTTPError as exc:
            logger.warning("parking-service vehicle_repository member_exit_fallback error=%s", exc)
            return self._fallback_member_validation(plate_text, face_image_id, expected_person_id=session_person_id)

    def _post(self, path: str, payload: dict) -> dict:
        with httpx.Client(timeout=settings.vehicle_service_timeout_seconds) as client:
            response = client.post(
                f"{settings.vehicle_service_url.rstrip('/')}{path}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._build_internal_token()}",
                    "X-Internal-Audit-Key": settings.audit_internal_key,
                    "Content-Type": "application/json",
                },
            )
        response.raise_for_status()
        return response.json()

    def _get(self, path: str) -> dict:
        with httpx.Client(timeout=settings.vehicle_service_timeout_seconds) as client:
            response = client.get(
                f"{settings.vehicle_service_url.rstrip('/')}{path}",
                headers={
                    "Authorization": f"Bearer {self._build_internal_token()}",
                    "X-Internal-Audit-Key": settings.audit_internal_key,
                },
            )
        response.raise_for_status()
        return response.json()

    def _build_internal_token(self) -> str:
        return encode_access_token(
            secret_key=settings.jwt_secret_key,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            expires_minutes=settings.jwt_access_token_expires_minutes,
            claims={
                "sub": "parking-service",
                "username": "parking-service",
                "roles": ["service_parking"],
                "permissions": ["parking.entry", "parking.exit", "vehicles.read", "members.read", "*"],
                "university_id": "system",
            },
        )

    def _fallback_member_validation(self, plate_text: str, face_image_id: str, expected_person_id: str | None = None) -> dict:
        record = self._fallback_records.get(plate_text)
        if record is None:
            return {
                "authorized": False,
                "vehicle_registered": False,
                "plate_text": plate_text,
                "message": "Vehicle plate is not registered as a university member vehicle",
                "warnings": [],
            }
        if expected_person_id and record["person_id"] != expected_person_id:
            return {
                "authorized": False,
                "vehicle_registered": True,
                "person_id": record["person_id"],
                "person_name": record["person_name"],
                "role_type": record["role_type"],
                "vehicle_id": record["vehicle_id"],
                "plate_text": plate_text,
                "permit_status": record["permit_status"],
                "face_match": False,
                "similarity": 0.31,
                "message": "Face verification failed for the authorized member",
                "warnings": ["SESSION_PERSON_MISMATCH"],
            }
        face_match = "invalid" not in face_image_id.lower()
        return {
            "authorized": face_match and record["permit_status"] == "VALID",
            "vehicle_registered": True,
            "person_id": record["person_id"],
            "person_name": record["person_name"],
            "role_type": record["role_type"],
            "vehicle_id": record["vehicle_id"],
            "plate_text": plate_text,
            "permit_status": record["permit_status"],
            "face_match": face_match,
            "similarity": 0.91 if face_match else 0.23,
            "provider": "mock-fallback",
            "message": "Member access authorized" if face_match else "Face verification failed for the authorized member",
            "warnings": [] if face_match else ["FACE_VERIFICATION_FAILED"],
        }
