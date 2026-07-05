import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from config import settings
from main import app


ASSETS_DIR = Path(__file__).parent / "assets"


class PlateDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.original_mode = settings.plate_service_mode

    def tearDown(self) -> None:
        settings.plate_service_mode = self.original_mode

    def test_mock_mode_detects_plate_from_simulated_image(self) -> None:
        settings.plate_service_mode = "mock"
        image_path = ASSETS_DIR / "visitor_ABC1234.jpg"

        with image_path.open("rb") as image_file:
            response = self.client.post(
                "/plates/detect",
                files={"image": (image_path.name, image_file, "image/jpeg")},
                data={"country_code": "EC"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["plate_text"], "ABC1234")
        self.assertEqual(payload["mode"], "mock")
        self.assertTrue(payload["valid_format"])
        self.assertGreaterEqual(payload["confidence"], 0.90)
        self.assertEqual(payload["bounding_box"]["width"], 260)

    def test_real_prepared_mode_uses_yolo_ocr_placeholders(self) -> None:
        settings.plate_service_mode = "real"
        image_path = ASSETS_DIR / "teacher_VIS0001.jpg"

        with image_path.open("rb") as image_file:
            response = self.client.post(
                "/plates/detect",
                files={"image": (image_path.name, image_file, "image/jpeg")},
                data={"country_code": "EC"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["plate_text"], "VIS0001")
        self.assertEqual(payload["mode"], "real")
        self.assertTrue(payload["valid_format"])
        self.assertGreaterEqual(payload["bounding_box"]["height"], 48)

    def test_empty_upload_is_rejected(self) -> None:
        settings.plate_service_mode = "mock"
        response = self.client.post(
            "/plates/detect",
            files={"image": ("empty.jpg", b"", "image/jpeg")},
            data={"country_code": "EC"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Image content is empty")


if __name__ == "__main__":
    unittest.main()
