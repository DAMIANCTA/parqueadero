import unittest

from fastapi.testclient import TestClient

from main import app


class ParkingEntryFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_visitor_entry_creates_inside_session_and_pending_payment(self) -> None:
        response = self.client.post(
            "/parking/entry",
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333331",
                "plate_text": "abc1234",
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
        self.assertTrue(payload["gate_command"]["published"])

    def test_registered_person_requires_authorized_plate(self) -> None:
        response = self.client.post(
            "/parking/entry",
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

    def test_low_liveness_rejects_entry(self) -> None:
        response = self.client.post(
            "/parking/entry",
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

    def test_unauthorized_registered_plate_is_rejected(self) -> None:
        response = self.client.post(
            "/parking/entry",
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "campus_id": "22222222-2222-2222-2222-222222222222",
                "gate_id": "33333333-3333-3333-3333-333333333331",
                "plate_text": "VIS0001",
                "face_image_id": "face-entry-004",
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
        self.assertIn("not authorized", payload["message"])


if __name__ == "__main__":
    unittest.main()
