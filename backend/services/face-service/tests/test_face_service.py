import unittest

from fastapi.testclient import TestClient

from config import settings
from main import app
from repositories.biometric_repository import BiometricRepository


class FaceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.original_mode = settings.face_service_mode
        self.original_provider = settings.face_real_provider
        BiometricRepository.reset()

    def tearDown(self) -> None:
        settings.face_service_mode = self.original_mode
        settings.face_real_provider = self.original_provider
        BiometricRepository.reset()

    def test_enroll_and_verify_match_in_mock_mode(self) -> None:
        settings.face_service_mode = "mock"
        enroll_response = self.client.post(
            "/faces/enroll",
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "person_id": "student-001",
                "image_reference": {
                    "bucket": "parking-raw-images",
                    "object_path": "faces/tests/student001-enroll.jpg",
                    "sha256_hash": "hash-enroll-001",
                    "image_type": "face_enroll",
                },
            },
        )

        self.assertEqual(enroll_response.status_code, 200)
        template_id = enroll_response.json()["template_id"]

        verify_response = self.client.post(
            "/faces/verify",
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "person_id": "student-001",
                "template_id": template_id,
                "probe_image_reference": {
                    "bucket": "parking-raw-images",
                    "object_path": "faces/tests/student001-probe.jpg",
                    "sha256_hash": "hash-probe-001",
                    "image_type": "face_verify",
                },
            },
        )

        self.assertEqual(verify_response.status_code, 200)
        payload = verify_response.json()
        self.assertTrue(payload["match"])
        self.assertGreaterEqual(payload["score"], settings.face_similarity_threshold)

    def test_compare_returns_no_match_for_different_subjects(self) -> None:
        settings.face_service_mode = "real"
        settings.face_real_provider = "deepface"

        response = self.client.post(
            "/faces/compare",
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "source_image_reference": {
                    "bucket": "parking-raw-images",
                    "object_path": "faces/tests/alice-enroll.jpg",
                    "image_type": "face_compare",
                },
                "target_image_reference": {
                    "bucket": "parking-raw-images",
                    "object_path": "faces/tests/bob-probe.jpg",
                    "image_type": "face_compare",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["match"])
        self.assertEqual(payload["mode"], "real")
        self.assertEqual(payload["model_name"], "deepface-prepared")

    def test_liveness_check_rejects_spoof_reference(self) -> None:
        settings.face_service_mode = "mock"
        response = self.client.post(
            "/faces/liveness-check",
            json={
                "university_id": "11111111-1111-1111-1111-111111111111",
                "person_id": "visitor-001",
                "challenge_type": "blink",
                "image_reference": {
                    "bucket": "parking-raw-images",
                    "object_path": "faces/tests/visitor001-spoof-photo.jpg",
                    "image_type": "face_liveness",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["passed"])
        self.assertLess(payload["score"], settings.face_liveness_threshold)


if __name__ == "__main__":
    unittest.main()
