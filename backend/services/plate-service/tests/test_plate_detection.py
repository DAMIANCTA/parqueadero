import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from config import settings
from services.plate_models import PlateDetectionOutcome, PlateTextCandidate, YoloDetectionDebug
from services.ocr_reader import OCRReaderService
from services.runtime_probe import RuntimeCapabilities
from services.plate_service import PlateService


ASSETS_DIR = Path(__file__).parent / "assets"


class PlateDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PlateService()
        self.original_mode = settings.plate_detection_mode

    def tearDown(self) -> None:
        settings.plate_detection_mode = self.original_mode

    def test_ocr_reader_prefers_rapidocr_without_trying_easyocr(self) -> None:
        original_engine = settings.plate_ocr_preferred_engine
        settings.plate_ocr_preferred_engine = "rapidocr"
        reader = OCRReaderService()
        capabilities = RuntimeCapabilities(
            opencv_available=True,
            easyocr_available=False,
            rapidocr_available=True,
            paddleocr_available=False,
            ocr_engine="rapidocr",
            model_path="models/plate_detector.pt",
            model_exists=True,
            plate_detection_mode="hybrid",
            plate_service_mode="hybrid",
            environment="local",
            min_confidence=0.70,
            errors={"easyocr": "No module named 'easyocr'"},
        )

        try:
            with patch("services.ocr_reader.probe_runtime_capabilities", return_value=capabilities), patch.object(
                reader,
                "_read_with_easyocr",
                side_effect=AssertionError("EasyOCR should not be used when rapidocr is preferred"),
            ), patch.object(
                reader,
                "_read_with_paddleocr",
                side_effect=AssertionError("PaddleOCR should not be used when rapidocr is preferred"),
            ), patch.object(
                reader,
                "_read_with_rapidocr",
                return_value=([PlateTextCandidate(text="AGH430", confidence=0.91)], "rapidocr"),
            ):
                candidates, warnings, provider, selected_engine = reader.read_plate_text([("raw", object())])

            self.assertEqual(selected_engine, "rapidocr")
            self.assertEqual(provider, "rapidocr")
            self.assertEqual(candidates[0].text, "AGH430")
            self.assertNotIn("OCR_ENGINE_FAILED", warnings)
        finally:
            settings.plate_ocr_preferred_engine = original_engine

    def test_ocr_reader_returns_warning_without_exception_when_preferred_engine_fails(self) -> None:
        original_engine = settings.plate_ocr_preferred_engine
        settings.plate_ocr_preferred_engine = "rapidocr"
        reader = OCRReaderService()
        capabilities = RuntimeCapabilities(
            opencv_available=True,
            easyocr_available=False,
            rapidocr_available=True,
            paddleocr_available=False,
            ocr_engine="rapidocr",
            model_path="models/plate_detector.pt",
            model_exists=True,
            plate_detection_mode="hybrid",
            plate_service_mode="hybrid",
            environment="local",
            min_confidence=0.70,
            errors={},
        )

        try:
            with patch("services.ocr_reader.probe_runtime_capabilities", return_value=capabilities), patch.object(
                reader,
                "_read_with_rapidocr",
                side_effect=RuntimeError("rapidocr crashed"),
            ):
                candidates, warnings, provider, selected_engine = reader.read_plate_text([("raw", object())])

            self.assertEqual(selected_engine, "rapidocr")
            self.assertEqual(provider, "none")
            self.assertEqual(candidates, [])
            self.assertIn("OCR_ENGINE_FAILED", warnings)
            self.assertNotIn("OCR_ENGINE_NOT_AVAILABLE", warnings)
        finally:
            settings.plate_ocr_preferred_engine = original_engine

    def test_mock_mode_detects_plate_from_simulated_image_upload(self) -> None:
        settings.plate_detection_mode = "mock"
        image_path = ASSETS_DIR / "visitor_ABC1234.jpg"

        outcome = self.service.detect_plate(
            image_id="upload-001",
            upload_bytes=image_path.read_bytes(),
            upload_filename=image_path.name,
            upload_content_type="image/jpeg",
            country_code="EC",
        )

        self.assertEqual(outcome.plate_text, "ABC1234")
        self.assertEqual(outcome.status, "DETECTED")
        self.assertTrue(outcome.valid_format)

    def test_json_mode_uses_registered_image_reference(self) -> None:
        settings.plate_detection_mode = "mock"
        image_path = ASSETS_DIR / "visitor_ABC1234.jpg"
        image_bytes = image_path.read_bytes()

        loaded_image = SimpleNamespace(
            image_id="img-minio-001",
            filename="visitor_ABC1234.jpg",
            content_type="image/jpeg",
            content=image_bytes,
            source="minio",
            object_name="2026/07/06/plate_entry/visitor_ABC1234.jpg",
        )

        with patch.object(self.service.image_source_service, "load_from_minio", return_value=loaded_image):
            outcome = self.service.detect_plate(
                image_id="img-minio-001",
                country_code="EC",
            )

        self.assertEqual(outcome.image_id, "img-minio-001")
        self.assertEqual(outcome.plate_text, "ABC1234")
        self.assertEqual(outcome.status, "DETECTED")
        self.assertGreaterEqual(len(outcome.candidates), 1)

    def test_not_detected_status_is_returned_for_unreadable_mock(self) -> None:
        settings.plate_detection_mode = "mock"

        outcome = self.service.detect_plate(
            image_id="bad-001",
            upload_bytes=b"NO_PLATE",
            upload_filename="UNREADABLE.jpg",
            upload_content_type="image/jpeg",
            country_code="EC",
        )

        self.assertEqual(outcome.status, "NOT_DETECTED")
        self.assertIsNone(outcome.plate_text)
        self.assertEqual(outcome.confidence, 0.0)

    def test_detect_batch_selects_most_repeated_plate(self) -> None:
        results = [
            PlateDetectionOutcome(
                status="DETECTED",
                plate_text="AGH430",
                confidence=0.84,
                image_id="img-1",
                bounding_box=None,
                candidates=[PlateTextCandidate(text="AGH430", confidence=0.84)],
                valid_format=True,
            ),
            PlateDetectionOutcome(
                status="DETECTED",
                plate_text="AGH430",
                confidence=0.91,
                image_id="img-2",
                bounding_box=None,
                candidates=[PlateTextCandidate(text="AGH430", confidence=0.91)],
                valid_format=True,
            ),
            PlateDetectionOutcome(
                status="LOW_CONFIDENCE",
                plate_text="A6H430",
                confidence=0.68,
                image_id="img-3",
                bounding_box=None,
                candidates=[PlateTextCandidate(text="A6H430", confidence=0.68)],
                valid_format=True,
            ),
        ]

        with patch.object(self.service, "detect_plate", side_effect=results):
            outcome = self.service.detect_plate_batch(
                image_ids=["img-1", "img-2", "img-3"],
                country_code="EC",
            )

        self.assertEqual(outcome.status, "DETECTED")
        self.assertEqual(outcome.plate_text, "AGH430")
        self.assertEqual(outcome.confidence, 0.91)
        self.assertEqual(len(outcome.results), 3)
        self.assertIn("INCONSISTENT_RESULT", outcome.warnings)

    def test_detect_batch_returns_not_detected_when_all_fail(self) -> None:
        results = [
            PlateDetectionOutcome(status="NOT_DETECTED", plate_text=None, confidence=0.0, image_id="img-1", bounding_box=None, warnings=["OCR_NO_TEXT"]),
            PlateDetectionOutcome(status="NOT_DETECTED", plate_text=None, confidence=0.0, image_id="img-2", bounding_box=None, warnings=["PLATE_REGION_NOT_FOUND"]),
            PlateDetectionOutcome(status="NOT_DETECTED", plate_text=None, confidence=0.0, image_id="img-3", bounding_box=None, warnings=["LOW_QUALITY_IMAGE"]),
        ]

        with patch.object(self.service, "detect_plate", side_effect=results):
            outcome = self.service.detect_plate_batch(
                image_ids=["img-1", "img-2", "img-3"],
                country_code="EC",
            )

        self.assertEqual(outcome.status, "NOT_DETECTED")
        self.assertIsNone(outcome.plate_text)
        self.assertEqual(outcome.confidence, 0.0)
        self.assertIn("BATCH_NOT_DETECTED", outcome.warnings)

    def test_detect_plate_uses_fallback_warning_when_ocr_succeeds_without_yolo_region(self) -> None:
        original_mode = settings.plate_detection_mode
        settings.plate_detection_mode = "hybrid"
        image_path = ASSETS_DIR / "visitor_ABC1234.jpg"
        image_bytes = image_path.read_bytes()
        loaded_image = SimpleNamespace(
            image_id="img-minio-ocr-fallback",
            filename="visitor_ABC1234.jpg",
            content_type="image/jpeg",
            content=image_bytes,
            source="minio",
            object_name="2026/07/07/plate_entry/visitor_ABC1234.jpg",
        )

        try:
            with patch.object(self.service.image_source_service, "load_from_minio", return_value=loaded_image), patch.object(
                self.service,
                "_decode_bgr",
                return_value=object(),
            ), patch.object(
                self.service.detector_service,
                "detect_plate_region",
                return_value=(
                    None,
                    ["PLATE_REGION_NOT_FOUND"],
                    0,
                    YoloDetectionDebug(model_exists=True, model_loaded=True, model_names=["license_plate"]),
                ),
            ), patch.object(
                self.service.ocr_reader,
                "read_plate_text",
                return_value=(
                    [PlateTextCandidate(text="ABC1234", confidence=1.0)],
                    [],
                    "rapidocr",
                    "rapidocr",
                ),
            ):
                outcome = self.service.detect_plate(image_id="img-minio-ocr-fallback", country_code="EC")

            self.assertEqual(outcome.status, "DETECTED")
            self.assertEqual(outcome.plate_text, "ABC1234")
            self.assertIn("YOLO_REGION_NOT_FOUND_OCR_FALLBACK_USED", outcome.warnings)
            self.assertNotIn("PLATE_REGION_NOT_FOUND", outcome.warnings)
        finally:
            settings.plate_detection_mode = original_mode


if __name__ == "__main__":
    unittest.main()
