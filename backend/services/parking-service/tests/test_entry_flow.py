import unittest

from fastapi.testclient import TestClient

from config import settings
from main import app
from security import encode_access_token


class ParkingEntryFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
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


if __name__ == "__main__":
    unittest.main()
