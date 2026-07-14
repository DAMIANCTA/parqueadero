import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from config import settings
from main import app
from repositories.parking_session_repository import ParkingSessionRepository
from routes.parking import entry_service
from security import encode_access_token


class ParkingEntryFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        ParkingSessionRepository.reset()
        self.entry_face_patcher = patch.object(
            entry_service.face_service,
            "validate_entry_face",
            side_effect=lambda **kwargs: {
                "accepted": "invalid" not in kwargs["face_image_id"].lower(),
                "detected": "invalid" not in kwargs["face_image_id"].lower(),
                "match": None,
                "similarity": None,
                "threshold": None,
                "image_id": kwargs["face_image_id"],
                "template_id": None,
                "provider": "mock-face-service",
                "model_name": "mock-face-model",
                "mode": "mock",
                "quality_score": kwargs.get("confidence_face", 0.95),
                "bounding_box": None,
                "embedding_size": 16 if "invalid" not in kwargs["face_image_id"].lower() else 0,
                "warnings": [] if "invalid" not in kwargs["face_image_id"].lower() else ["FACE_NOT_DETECTED"],
            },
        )
        self.entry_iot_patcher = patch.object(
            entry_service.iot_repository,
            "open_gate",
            return_value={"gate_id": "gate-test", "command": "open", "published": True},
        )
        self.detect_vehicle_patcher = patch.object(
            entry_service.vehicle_authorization_repository,
            "detect_registered_vehicle",
            side_effect=lambda **kwargs: {
                "found": kwargs["plate_text"] == "ABC1234",
                "vehicle_id": "vehicle-001" if kwargs["plate_text"] == "ABC1234" else None,
                "plate_text": kwargs["plate_text"],
                "authorized_people": [{"id": "person-student-001", "full_name": "Ana Belen Torres", "role_type": "STUDENT"}]
                if kwargs["plate_text"] == "ABC1234"
                else [],
                "message": "Vehicle plate is registered" if kwargs["plate_text"] == "ABC1234" else "Vehicle plate is not registered",
            },
        )
        self.member_entry_patcher = patch.object(
            entry_service.vehicle_authorization_repository,
            "validate_member_entry",
            side_effect=lambda **kwargs: {
                "authorized": "invalid" not in kwargs["face_image_id"].lower(),
                "vehicle_registered": True,
                "person_id": "person-student-001",
                "person_name": "Ana Belen Torres",
                "role_type": "STUDENT",
                "vehicle_id": "vehicle-001",
                "plate_text": kwargs["plate_text"],
                "permit_status": "VALID",
                "face_match": "invalid" not in kwargs["face_image_id"].lower(),
                "similarity": 0.91 if "invalid" not in kwargs["face_image_id"].lower() else 0.23,
                "provider": "mock-face-service",
                "message": "Member access authorized" if "invalid" not in kwargs["face_image_id"].lower() else "Face verification failed for the authorized member",
                "warnings": [] if "invalid" not in kwargs["face_image_id"].lower() else ["FACE_VERIFICATION_FAILED"],
            },
        )
        for patcher in (
            self.entry_face_patcher,
            self.entry_iot_patcher,
            self.detect_vehicle_patcher,
            self.member_entry_patcher,
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        token = encode_access_token(
            secret_key=settings.jwt_secret_key,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            expires_minutes=30,
            claims={
                "sub": "test-gate",
                "username": "gate.operator",
                "roles": ["gate_operator"],
                "permissions": ["parking.entry", "parking.exit", "faces.verify", "faces.compare"],
                "university_id": "11111111-1111-1111-1111-111111111111",
            },
        )
        self.headers = {"Authorization": f"Bearer {token}"}

    def test_visitor_entry_creates_inside_session_and_pending_payment(self) -> None:
        response = self.client.post(
            "/parking/entry",
            headers=self.headers,
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333331",
                "plate_text": "vis0001",
                "face_image_id": "face-entry-001",
                "liveness_score": 0.95,
                "person_type": "visitor",
                "confidence_plate": 0.97,
                "confidence_face": 0.98,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["authorized"])
        self.assertEqual(payload["status"], "AUTHORIZED")
        self.assertEqual(payload["session"]["session_status"], "INSIDE")
        self.assertEqual(payload["session"]["payment_status"], "PENDING")
        self.assertEqual(payload["session"]["access_type"], "VISITOR")
        self.assertTrue(payload["gate_command"]["published"])

    def test_registered_member_entry_is_authorized_and_sets_not_required_payment(self) -> None:
        response = self.client.post(
            "/parking/entry",
            headers=self.headers,
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333331",
                "plate_text": "ABC1234",
                "face_image_id": "face-entry-002",
                "liveness_score": 0.94,
                "person_type": "student",
                "confidence_plate": 0.94,
                "confidence_face": 0.96,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["authorized"])
        self.assertEqual(payload["session"]["payment_status"], "NOT_REQUIRED")
        self.assertEqual(payload["session"]["access_type"], "MEMBER")
        self.assertEqual(payload["session"]["person_name"], "Ana Belen Torres")

    def test_low_liveness_rejects_entry(self) -> None:
        response = self.client.post(
            "/parking/entry",
            headers=self.headers,
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333331",
                "plate_text": "ABC1234",
                "face_image_id": "face-entry-003",
                "liveness_score": 0.30,
                "person_type": "student",
                "confidence_plate": 0.95,
                "confidence_face": 0.95,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["authorized"])
        self.assertEqual(payload["status"], "REJECTED")
        self.assertEqual(payload["message"], "Liveness score too low")
        self.assertEqual(payload["gate_command"]["command"], "deny")

    def test_registered_member_plate_is_rejected_when_face_fails(self) -> None:
        response = self.client.post(
            "/parking/entry",
            headers=self.headers,
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333331",
                "plate_text": "ABC1234",
                "face_image_id": "invalid-face-entry-004",
                "liveness_score": 0.88,
                "person_type": "teacher",
                "confidence_plate": 0.92,
                "confidence_face": 0.95,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["authorized"])
        self.assertEqual(payload["status"], "REJECTED")
        self.assertIn("Face", payload["message"])
        self.assertEqual(payload["gate_command"]["command"], "deny")

    def test_duplicate_entry_is_rejected(self) -> None:
        response = self.client.post(
            "/parking/entry",
            headers=self.headers,
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333331",
                "plate_text": "VISPEND",
                "face_image_id": "face-entry-duplicate-001",
                "liveness_score": 0.95,
                "person_type": "visitor",
                "confidence_plate": 0.97,
                "confidence_face": 0.98,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["authorized"])
        self.assertEqual(payload["status"], "REJECTED")
        self.assertEqual(payload["message"], "El vehiculo ya se encuentra dentro")
        self.assertEqual(payload["gate_command"]["command"], "deny")


if __name__ == "__main__":
    unittest.main()
