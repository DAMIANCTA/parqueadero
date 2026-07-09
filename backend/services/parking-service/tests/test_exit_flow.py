import unittest
from datetime import datetime, timedelta, UTC
from unittest.mock import patch

from fastapi.testclient import TestClient

from config import settings
from main import app
from security import encode_access_token


class ParkingExitFlowTests(unittest.TestCase):
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

    def test_visitor_exit_requires_paid_session_and_matching_face(self) -> None:
        response = self.client.post(
            "/parking/exit",
            headers=self.headers,
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333332",
                "plate_text": "VIS1234",
                "face_image_id": "face-exit-001",
                "liveness_score": 0.96,
                "confidence_plate": 0.98,
                "confidence_face": 0.97,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["authorized"])
        self.assertEqual(payload["session"]["session_status"], "OUTSIDE")
        self.assertEqual(payload["session"]["payment_status"], "PAID")
        self.assertIsNone(payload["incident_id"])

    def test_visitor_exit_rejects_when_payment_pending(self) -> None:
        response = self.client.post(
            "/parking/exit",
            headers=self.headers,
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333332",
                "plate_text": "VISPEND",
                "face_image_id": "face-exit-002",
                "liveness_score": 0.96,
                "confidence_plate": 0.98,
                "confidence_face": 0.97,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["authorized"])
        self.assertEqual(payload["status"], "REJECTED")
        self.assertEqual(payload["message"], "Payment status is not PAID")
        self.assertIsNotNone(payload["incident_id"])

    def test_registered_exit_authorizes_when_plate_face_and_permission_are_valid(self) -> None:
        response = self.client.post(
            "/parking/exit",
            headers=self.headers,
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333332",
                "plate_text": "ABC1234",
                "face_image_id": "face-student-001",
                "liveness_score": 0.91,
                "confidence_plate": 0.95,
                "confidence_face": 0.96,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["authorized"])
        self.assertEqual(payload["session"]["payment_status"], "NOT_REQUIRED")
        self.assertEqual(payload["session"]["access_type"], "MEMBER")
        self.assertTrue(payload["gate_command"]["published"])

    def test_registered_exit_rejects_when_permission_is_invalid(self) -> None:
        response = self.client.post(
            "/parking/exit",
            headers=self.headers,
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333332",
                "plate_text": "EXP2026",
                "face_image_id": "face-expired-001",
                "liveness_score": 0.92,
                "confidence_plate": 0.95,
                "confidence_face": 0.96,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["authorized"])
        self.assertEqual(payload["message"], "Permission is not valid")

    def test_visitor_exit_rejects_when_payment_grace_period_expired(self) -> None:
        with patch(
            "routes.parking.exit_service.payment_repository.get_status_by_plate",
            return_value={
                "found": True,
                "payment_status": "PAID",
                "paid_at": (datetime.now(UTC) - timedelta(minutes=20)).isoformat(),
                "paid_amount": 1.50,
                "payment_valid_until": (datetime.now(UTC) - timedelta(minutes=5)).isoformat(),
            },
        ):
            response = self.client.post(
                "/parking/exit",
                headers=self.headers,
                json={
                    "university_id": "11111111-1111-1111-1111-111111111111",
                    "campus_id": "22222222-2222-2222-2222-222222222222",
                    "gate_id": "33333333-3333-3333-3333-333333333332",
                    "plate_text": "VIS1234",
                    "face_image_id": "face-exit-001",
                    "liveness_score": 0.96,
                    "confidence_plate": 0.98,
                    "confidence_face": 0.97,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["authorized"])
        self.assertEqual(payload["message"], "Payment grace period expired")


if __name__ == "__main__":
    unittest.main()
