from config import settings
from schemas.plates import BoundingBox, PlateDetectResponse
from services.mock_plate_detector import MockPlateDetector
from services.mock_plate_ocr import MockPlateOcr
from services.ocr_prepared_service import OcrPreparedService
from services.plate_format_validator import PlateFormatValidator
from services.plate_models import PlateImage
from services.plate_normalizer import PlateNormalizer
from services.yolo_prepared_plate_detector import YoloPreparedPlateDetector


class PlateDetectionService:
    def __init__(self) -> None:
        self.normalizer = PlateNormalizer()
        self.validator = PlateFormatValidator()

    def detect_plate(
        self,
        *,
        filename: str,
        content_type: str,
        content: bytes,
        country_code: str | None,
    ) -> PlateDetectResponse:
        image = PlateImage(
            filename=filename or "upload.jpg",
            content_type=content_type or "application/octet-stream",
            content=content,
            country_code=country_code or settings.plate_default_country_code,
        )
        detector, ocr = self._resolve_pipeline()
        detection = detector.detect(image)
        ocr_result = ocr.read(image, detection)
        normalized = self.normalizer.normalize(ocr_result.text)
        is_valid = self.validator.is_valid(normalized)
        confidence = min(detection.confidence, ocr_result.confidence)
        if not is_valid:
            confidence = min(confidence, 0.60)

        return PlateDetectResponse(
            plate_text=normalized,
            confidence=round(confidence, 4),
            bounding_box=BoundingBox(
                x=detection.x,
                y=detection.y,
                width=detection.width,
                height=detection.height,
            ),
            mode=settings.plate_service_mode,
            valid_format=is_valid,
        )

    def _resolve_pipeline(self):
        if settings.plate_service_mode.lower() == "real":
            return YoloPreparedPlateDetector(), OcrPreparedService()
        return MockPlateDetector(), MockPlateOcr()
