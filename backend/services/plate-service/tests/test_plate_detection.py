import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from config import settings
from main import app


ASSETS_DIR = Path(__file__).parent / "assets"


class PlateDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.original_mode = settings.plate_detection_mode

    def tearDown(self) -> None:
        settings.plate_detection_mode = self.original_mode

    def test_mock_mode_detects_plate_from_simulated_image_upload(self) -> None:
        settings.plate_detection_mode = "mock"
        image_path = ASSETS_DIR / "visitor_ABC1234.jpg"

        with image_path.open("rb") as image_file, patch(
            "security.decode_access_token",
            return_value={"permissions": ["plates.detect", "*"], "sub": "test"},
        ):
            response = self.client.post(
                "/plates/detect",
                headers={"Authorization": "Bearer fake-token"},
                files={"image": (image_path.name, image_file, "image/jpeg")},
                data={"country_code": "EC"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["plate_text"], "ABC1234")
        self.assertEqual(payload["status"], "DETECTED")
        self.assertEqual(payload["source"], "upload")

    def test_json_mode_uses_registered_image_reference(self) -> None:
        settings.plate_detection_mode = "mock"
        image_path = ASSETS_DIR / "visitor_ABC1234.jpg"
        image_bytes = image_path.read_bytes()

        with patch(
            "routes.plates.image_source_service.load_from_minio",
            return_value=type(
                "LoadedImagePayload",
                (),
                {
                    "image_id": "img-minio-001",
                    "filename": "visitor_ABC1234.jpg",
                    "content_type": "image/jpeg",
                    "content": image_bytes,
                    "source": "minio",
                    "object_name": "2026/07/06/plate_entry/visitor_ABC1234.jpg",
                },
            )(),
        ), patch("security.decode_access_token", return_value={"permissions": ["plates.detect", "*"], "sub": "test"}):
            response = self.client.post(
                "/plates/detect",
                json={
                    "image_id": "img-minio-001",
                    "university_id": "uce",
                    "campus_id": "matriz",
                    "gate_id": "norte",
                },
                headers={"Authorization": "Bearer fake-token"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["image_id"], "img-minio-001")
        self.assertEqual(payload["source"], "minio")
        self.assertEqual(payload["plate_text"], "ABC1234")
        self.assertEqual(payload["status"], "DETECTED")
        self.assertGreaterEqual(len(payload["candidates"]), 1)

    def test_not_detected_status_is_returned_for_unreadable_mock(self) -> None:
        settings.plate_detection_mode = "mock"

        with patch("security.decode_access_token", return_value={"permissions": ["plates.detect", "*"], "sub": "test"}):
            response = self.client.post(
                "/plates/detect",
                headers={"Authorization": "Bearer fake-token"},
                files={"image": ("UNREADABLE.jpg", b"NO_PLATE", "image/jpeg")},
                data={"country_code": "EC"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "NOT_DETECTED")
        self.assertEqual(payload["plate_text"], "")
        self.assertEqual(payload["confidence"], 0.0)


if __name__ == "__main__":
    unittest.main()
