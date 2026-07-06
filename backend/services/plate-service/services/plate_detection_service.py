from schemas.plates import BoundingBox, PlateCandidateResponse, PlateDetectResponse
from config import settings
from services.mock_plate_detector import MockPlateDetector
from services.mock_plate_ocr import MockPlateOcr
from services.ocr_prepared_service import OcrPreparedService
from services.plate_format_validator import PlateFormatValidator
from services.plate_models import PlateImage, PlateTextCandidate
from services.plate_normalizer import PlateNormalizer
from services.yolo_prepared_plate_detector import YoloPreparedPlateDetector


class PlateDetectionService:
    def __init__(self) -> None:
        self.normalizer = PlateNormalizer()
        self.validator = PlateFormatValidator()

    def detect_plate(
        self,
        *,
        image_id: str,
        filename: str,
        content_type: str,
        content: bytes,
        source: str,
        country_code: str | None,
        object_name: str | None = None,
    ) -> PlateDetectResponse:
        image = PlateImage(
            image_id=image_id,
            filename=filename or "upload.jpg",
            content_type=content_type or "application/octet-stream",
            content=content,
            country_code=country_code or settings.plate_default_country_code,
            source=source,
            object_name=object_name,
        )
        detector, ocr = self._resolve_pipeline()
        detection = detector.detect(image)
        ocr_result = ocr.read(image, detection)

        normalized = self.normalizer.normalize(ocr_result.text)
        candidates = self._normalize_candidates(ocr_result.candidates or [PlateTextCandidate(text=ocr_result.text, confidence=ocr_result.confidence)])
        valid_format = self.validator.is_valid(normalized)
        confidence = 0.0 if not normalized else min(detection.confidence, ocr_result.confidence)
        if not valid_format:
            confidence = min(confidence, 0.60)

        status = self._resolve_status(normalized, valid_format, confidence)
        return PlateDetectResponse(
            image_id=image.image_id,
            plate_text=normalized,
            confidence=round(confidence, 4),
            bounding_box=BoundingBox(
                x=detection.x,
                y=detection.y,
                width=detection.width,
                height=detection.height,
            ),
            candidates=[
                PlateCandidateResponse(text=candidate.text, confidence=round(candidate.confidence, 4))
                for candidate in candidates
            ],
            status=status,
            mode=settings.effective_plate_detection_mode,
            valid_format=valid_format,
            source=image.source,
            detector_provider=detection.provider,
            ocr_provider=ocr_result.provider,
        )

    def detect_plate_region(self, image: PlateImage):
        detector, _ = self._resolve_pipeline()
        return detector.detect(image)

    def read_plate_text(self, image: PlateImage, detection):
        _, ocr = self._resolve_pipeline()
        return ocr.read(image, detection)

    def normalize_plate_text(self, text: str) -> str:
        return self.normalizer.normalize(text)

    def validate_plate_format(self, text: str) -> bool:
        return self.validator.is_valid(text)

    def _normalize_candidates(self, candidates: list[PlateTextCandidate]) -> list[PlateTextCandidate]:
        normalized: list[PlateTextCandidate] = []
        seen: set[str] = set()
        for candidate in candidates:
            text = self.normalizer.normalize(candidate.text)
            if not text or text in seen:
                continue
            seen.add(text)
            normalized.append(PlateTextCandidate(text=text, confidence=max(0.0, min(candidate.confidence, 1.0))))

        normalized.sort(key=lambda item: item.confidence, reverse=True)
        return normalized[:5]

    def _resolve_status(self, plate_text: str, valid_format: bool, confidence: float) -> str:
        if not plate_text or not valid_format:
            return "NOT_DETECTED"
        if confidence < settings.plate_auto_accept_confidence:
            return "LOW_CONFIDENCE"
        return "DETECTED"

    def _resolve_pipeline(self):
        if settings.effective_plate_detection_mode == "real":
            return YoloPreparedPlateDetector(), OcrPreparedService()
        return MockPlateDetector(), MockPlateOcr()
