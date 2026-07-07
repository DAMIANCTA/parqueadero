from abc import ABC, abstractmethod
from typing import Any

from services.plate_models import DetectionCandidate, OcrCandidate, PlateImage
from services.plate_models import PlateTextCandidate


class OcrReader(ABC):
    @abstractmethod
    def read(self, image: PlateImage, detection: DetectionCandidate) -> OcrCandidate:
        raise NotImplementedError


class OCRReaderService:
    def read_plate_text(self, image_variants: list[tuple[str, Any]]) -> tuple[list[PlateTextCandidate], list[str], str]:
        warnings: list[str] = []
        candidates: list[PlateTextCandidate] = []

        provider = "none"
        easyocr_error: Exception | None = None
        try:
            easyocr_candidates, provider = self._read_with_easyocr(image_variants)
            candidates.extend(easyocr_candidates)
        except Exception as exc:  # pragma: no cover - runtime dependency path
            easyocr_error = exc
            warnings.append("EASYOCR_NOT_AVAILABLE")

        if candidates:
            return candidates, warnings, provider

        try:
            paddle_candidates, provider = self._read_with_paddleocr(image_variants)
            candidates.extend(paddle_candidates)
            warnings = [warning for warning in warnings if warning != "EASYOCR_NOT_AVAILABLE"]
        except Exception:  # pragma: no cover - runtime dependency path
            warnings.append("PADDLEOCR_NOT_AVAILABLE")

        if not candidates and easyocr_error is not None:
            warnings.append("OCR_ENGINE_NOT_AVAILABLE")

        return candidates, self._unique(warnings), provider

    def _read_with_easyocr(self, image_variants: list[tuple[str, Any]]) -> tuple[list[PlateTextCandidate], str]:
        import easyocr  # type: ignore

        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        candidates: list[PlateTextCandidate] = []
        for _, variant in image_variants:
            for item in reader.readtext(variant, detail=1, paragraph=False):
                if len(item) < 3:
                    continue
                _, text, confidence = item
                candidates.append(
                    PlateTextCandidate(
                        text=str(text),
                        confidence=float(confidence or 0.0),
                    )
                )
        return candidates, "easyocr"

    def _read_with_paddleocr(self, image_variants: list[tuple[str, Any]]) -> tuple[list[PlateTextCandidate], str]:
        from paddleocr import PaddleOCR  # type: ignore

        ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
        candidates: list[PlateTextCandidate] = []
        for _, variant in image_variants:
            result = ocr.ocr(variant, cls=False) or []
            for line in result:
                for item in line or []:
                    if len(item) < 2:
                        continue
                    text, confidence = item[1]
                    candidates.append(
                        PlateTextCandidate(
                            text=str(text),
                            confidence=float(confidence or 0.0),
                        )
                    )
        return candidates, "paddleocr"

    def _unique(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
        return ordered
