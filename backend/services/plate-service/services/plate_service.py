import logging
from io import BytesIO
from typing import Any

from PIL import Image

from config import settings
from services.image_quality import ImageQualityService
from services.image_source_service import ImageSourceService
from services.mock_plate_detector import MockPlateDetector
from services.mock_plate_ocr import MockPlateOcr
from services.ocr_reader import OCRReaderService
from services.plate_cropper import PlateCropper
from services.plate_detector_yolo import YoloPlateDetectorService
from services.plate_models import (
    DetectionCandidate,
    OcrCandidate,
    PlateBatchDetectionOutcome,
    PlateDetectionOutcome,
    PlateImage,
    PlateTextCandidate,
)
from services.plate_normalizer import PlateNormalizer
from services.plate_format_validator import PlateFormatValidator
from services.plate_preprocessor import PlatePreprocessor


logger = logging.getLogger(__name__)


class PlateService:
    def __init__(self) -> None:
        self.image_source_service = ImageSourceService()
        self.image_quality_service = ImageQualityService()
        self.detector_service = YoloPlateDetectorService()
        self.cropper = PlateCropper()
        self.preprocessor = PlatePreprocessor()
        self.ocr_reader = OCRReaderService()
        self.normalizer = PlateNormalizer()
        self.validator = PlateFormatValidator()
        self.mock_detector = MockPlateDetector()
        self.mock_ocr = MockPlateOcr()

    def detect_plate(
        self,
        *,
        image_id: str,
        country_code: str | None = None,
        bucket: str | None = None,
        object_name: str | None = None,
        upload_bytes: bytes | None = None,
        upload_filename: str | None = None,
        upload_content_type: str | None = None,
    ) -> PlateDetectionOutcome:
        image = self._load_image(
            image_id=image_id,
            bucket=bucket,
            object_name=object_name,
            upload_bytes=upload_bytes,
            upload_filename=upload_filename,
            upload_content_type=upload_content_type,
        )
        logger.info("plate_detect start image_id=%s object_name=%s source=%s", image.image_id, image.object_name, image.source)

        if settings.effective_plate_detection_mode == "mock":
            outcome = self._detect_mock(image)
            self._log_outcome(image, outcome, quality_score=None)
            return outcome

        quality = self.image_quality_service.evaluate(image.content)
        logger.info(
            "plate_detect image_id=%s image_size=%sx%s quality_score=%.4f quality_warnings=%s",
            image.image_id,
            quality.width,
            quality.height,
            quality.quality_score,
            quality.warnings,
        )

        image_bgr = self._decode_bgr(image.content)
        if image_bgr is None:
            outcome = PlateDetectionOutcome(
                status="NOT_DETECTED",
                plate_text=None,
                confidence=0.0,
                image_id=image.image_id,
                bounding_box=None,
                warnings=["INVALID_IMAGE"],
            )
            self._log_outcome(image, outcome, quality_score=quality.quality_score)
            return outcome

        detection, detector_warnings = self._detect_region(image_bgr)
        warnings = list(dict.fromkeys([*quality.warnings, *detector_warnings]))
        logger.info(
            "plate_detect image_id=%s bounding_box_found=%s detector_warnings=%s",
            image.image_id,
            detection is not None,
            detector_warnings,
        )

        crop_source = self.cropper.crop(image_bgr, detection) if detection else image_bgr
        if crop_source is None:
            warnings.append("PLATE_REGION_NOT_FOUND")
            outcome = PlateDetectionOutcome(
                status="NOT_DETECTED",
                plate_text=None,
                confidence=0.0,
                image_id=image.image_id,
                bounding_box=None,
                warnings=list(dict.fromkeys(warnings)),
                detector_provider=detection.provider if detection else "none",
                ocr_provider="none",
            )
            self._log_outcome(image, outcome, quality_score=quality.quality_score)
            return outcome

        variants = self.preprocessor.create_variants(crop_source)
        ocr_candidates, ocr_warnings, ocr_provider = self.ocr_reader.read_plate_text(variants)
        warnings.extend(ocr_warnings)
        logger.info(
            "plate_detect image_id=%s ocr_raw=%s",
            image.image_id,
            [candidate.text for candidate in ocr_candidates],
        )

        normalized_candidates = self._normalize_candidates(ocr_candidates)
        if not normalized_candidates:
            warnings.append("OCR_NO_TEXT")
            outcome = PlateDetectionOutcome(
                status="NOT_DETECTED",
                plate_text=None,
                confidence=0.0,
                image_id=image.image_id,
                bounding_box=self._to_bbox(detection),
                candidates=[],
                warnings=list(dict.fromkeys(warnings)),
                valid_format=False,
                detector_provider=detection.provider if detection else "none",
                ocr_provider=ocr_provider,
            )
            self._log_outcome(image, outcome, quality_score=quality.quality_score)
            return outcome

        best = normalized_candidates[0]
        valid_format = self.validator.is_valid(best.text)
        if not valid_format:
            warnings.append("INVALID_PLATE_FORMAT")

        confidence = min(best.confidence, detection.confidence if detection else best.confidence)
        confidence = round(max(0.0, min(confidence, 1.0)), 4)
        if not valid_format:
            confidence = min(confidence, 0.60)

        if not detection:
            warnings.append("MODEL_NOT_FOUND" if "MODEL_NOT_FOUND" in detector_warnings else "PLATE_REGION_NOT_FOUND")

        status = self._resolve_status(best.text, confidence, valid_format)
        outcome = PlateDetectionOutcome(
            status=status,
            plate_text=best.text if valid_format else None,
            confidence=confidence if valid_format else 0.0,
            image_id=image.image_id,
            bounding_box=self._to_bbox(detection),
            candidates=normalized_candidates,
            warnings=list(dict.fromkeys(warnings)),
            valid_format=valid_format,
            detector_provider=detection.provider if detection else "none",
            ocr_provider=ocr_provider,
        )
        self._log_outcome(image, outcome, quality_score=quality.quality_score)
        return outcome

    def detect_plate_batch(
        self,
        *,
        image_ids: list[str],
        country_code: str | None = None,
    ) -> PlateBatchDetectionOutcome:
        logger.info("plate_detect_batch start image_ids=%s", image_ids)
        results = [
            self.detect_plate(
                image_id=image_id,
                country_code=country_code,
            )
            for image_id in image_ids
        ]

        valid_results = [
            result for result in results if result.plate_text and result.valid_format and result.status != "NOT_DETECTED"
        ]
        warnings = self._collect_batch_warnings(results)
        if not valid_results:
            warnings.append("BATCH_NOT_DETECTED")
            outcome = PlateBatchDetectionOutcome(
                status="NOT_DETECTED",
                plate_text=None,
                confidence=0.0,
                results=results,
                warnings=self._unique(warnings),
            )
            logger.info("plate_detect_batch end status=%s plate_text=%s confidence=%.4f warnings=%s", outcome.status, outcome.plate_text, outcome.confidence, outcome.warnings)
            return outcome

        grouped: dict[str, list[PlateDetectionOutcome]] = {}
        for result in valid_results:
            grouped.setdefault(result.plate_text or "", []).append(result)

        ranked_groups = sorted(
            grouped.items(),
            key=lambda item: (
                len(item[1]),
                max(candidate.confidence for candidate in item[1]),
                sum(candidate.confidence for candidate in item[1]) / len(item[1]),
            ),
            reverse=True,
        )
        winning_plate, winning_results = ranked_groups[0]
        final_confidence = round(max(result.confidence for result in winning_results), 4)

        if len(grouped) > 1:
            warnings.append("INCONSISTENT_RESULT")

        status = "DETECTED" if final_confidence >= settings.plate_auto_accept_confidence else "LOW_CONFIDENCE"
        outcome = PlateBatchDetectionOutcome(
            status=status,
            plate_text=winning_plate,
            confidence=final_confidence,
            results=results,
            warnings=self._unique(warnings),
        )
        logger.info(
            "plate_detect_batch end status=%s plate_text=%s confidence=%.4f warnings=%s grouped=%s",
            outcome.status,
            outcome.plate_text,
            outcome.confidence,
            outcome.warnings,
            {plate: len(items) for plate, items in grouped.items()},
        )
        return outcome

    def _load_image(
        self,
        *,
        image_id: str,
        bucket: str | None,
        object_name: str | None,
        upload_bytes: bytes | None,
        upload_filename: str | None,
        upload_content_type: str | None,
    ) -> PlateImage:
        if upload_bytes is not None:
            loaded = self.image_source_service.load_from_upload(
                filename=upload_filename or "upload.jpg",
                content_type=upload_content_type or "application/octet-stream",
                content=upload_bytes,
                image_id=image_id,
            )
        else:
            loaded = self.image_source_service.load_from_minio(
                image_id=image_id,
                bucket=bucket,
                object_name=object_name,
            )
        return PlateImage(
            image_id=loaded.image_id,
            filename=loaded.filename,
            content_type=loaded.content_type,
            content=loaded.content,
            country_code="EC",
            source=loaded.source,
            object_name=loaded.object_name,
        )

    def _detect_mock(self, image: PlateImage) -> PlateDetectionOutcome:
        detection = self.mock_detector.detect(image)
        ocr_result = self.mock_ocr.read(image, detection)
        normalized_candidates = self._normalize_candidates(ocr_result.candidates)
        best = normalized_candidates[0] if normalized_candidates else None
        valid_format = best is not None and self.validator.is_valid(best.text)
        confidence = round(min(detection.confidence, best.confidence if best else 0.0), 4)
        warnings = [] if best and valid_format else ["PLATE_REGION_NOT_FOUND"]
        status = self._resolve_status(best.text if best else None, confidence, valid_format)
        return PlateDetectionOutcome(
            status=status,
            plate_text=best.text if best and valid_format else None,
            confidence=confidence if best and valid_format else 0.0,
            image_id=image.image_id,
            bounding_box=self._to_bbox(detection),
            candidates=normalized_candidates,
            warnings=warnings,
            valid_format=valid_format,
            detector_provider=detection.provider,
            ocr_provider=ocr_result.provider,
        )

    def _detect_region(self, image_bgr: Any) -> tuple[DetectionCandidate | None, list[str]]:
        mode = settings.effective_plate_detection_mode
        detection, warnings = self.detector_service.detect_plate_region(image_bgr)
        if mode == "real":
            if "MODEL_NOT_FOUND" in warnings:
                raise RuntimeError("MODEL_NOT_FOUND")
            if "YOLO_NOT_AVAILABLE" in warnings:
                raise RuntimeError("YOLO_NOT_AVAILABLE")
        return detection, warnings

    def _normalize_candidates(self, raw_candidates: list[PlateTextCandidate]) -> list[PlateTextCandidate]:
        normalized: list[PlateTextCandidate] = []
        seen: set[str] = set()
        for candidate in raw_candidates:
            text = self.normalizer.normalize(candidate.text)
            if not text or text in seen:
                continue
            seen.add(text)
            normalized.append(
                PlateTextCandidate(
                    text=text,
                    confidence=round(max(0.0, min(candidate.confidence, 1.0)), 4),
                )
            )

        normalized.sort(key=lambda item: item.confidence, reverse=True)
        return normalized[:5]

    def _resolve_status(self, plate_text: str | None, confidence: float, valid_format: bool) -> str:
        if not plate_text or not valid_format:
            return "NOT_DETECTED"
        if confidence < settings.plate_auto_accept_confidence:
            return "LOW_CONFIDENCE"
        return "DETECTED"

    def _collect_batch_warnings(self, results: list[PlateDetectionOutcome]) -> list[str]:
        warnings: list[str] = []
        for result in results:
            warnings.extend(result.warnings)
        return self._unique(warnings)

    def _unique(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_items: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            unique_items.append(item)
        return unique_items

    def _decode_bgr(self, image_bytes: bytes):
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore

            buffer = np.frombuffer(image_bytes, dtype=np.uint8)
            return cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        except Exception:
            try:
                image = Image.open(BytesIO(image_bytes)).convert("RGB")
                import numpy as np  # type: ignore

                return np.array(image)[:, :, ::-1].copy()
            except Exception:
                return None

    def _to_bbox(self, detection: DetectionCandidate | None) -> dict | None:
        if detection is None:
            return None
        return {
            "x": detection.x,
            "y": detection.y,
            "width": detection.width,
            "height": detection.height,
        }

    def _log_outcome(self, image: PlateImage, outcome: PlateDetectionOutcome, *, quality_score: float | None) -> None:
        logger.info(
            "plate_detect end image_id=%s object_name=%s normalized_text=%s confidence=%.4f quality_score=%s status=%s warnings=%s",
            image.image_id,
            image.object_name,
            outcome.plate_text,
            outcome.confidence,
            quality_score,
            outcome.status,
            outcome.warnings,
        )
