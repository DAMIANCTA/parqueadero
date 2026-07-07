from abc import ABC, abstractmethod
import logging
from typing import Any

from services.plate_models import DetectionCandidate, OcrCandidate, PlateImage
from services.plate_models import PlateTextCandidate
from services.runtime_probe import probe_runtime_capabilities


logger = logging.getLogger(__name__)


class OcrReader(ABC):
    @abstractmethod
    def read(self, image: PlateImage, detection: DetectionCandidate) -> OcrCandidate:
        raise NotImplementedError


class OCRReaderService:
    def read_plate_text(self, image_variants: list[tuple[str, Any]]) -> tuple[list[PlateTextCandidate], list[str], str]:
        warnings: list[str] = []
        candidates: list[PlateTextCandidate] = []
        provider = "none"

        capabilities = probe_runtime_capabilities()
        if not capabilities.easyocr_available:
            warnings.append("EASYOCR_NOT_AVAILABLE")
            logger.warning("ocr_reader dependency_unavailable engine=easyocr error=%s", capabilities.errors.get("easyocr", "unknown"))
        if not capabilities.rapidocr_available:
            warnings.append("RAPIDOCR_NOT_AVAILABLE")
            logger.warning("ocr_reader dependency_unavailable engine=rapidocr error=%s", capabilities.errors.get("rapidocr", "unknown"))
        if not capabilities.paddleocr_available:
            warnings.append("PADDLEOCR_NOT_AVAILABLE")
            logger.warning("ocr_reader dependency_unavailable engine=paddleocr error=%s", capabilities.errors.get("paddleocr", "unknown"))

        for reader_name, reader in (
            ("easyocr", self._read_with_easyocr),
            ("rapidocr", self._read_with_rapidocr),
            ("paddleocr", self._read_with_paddleocr),
        ):
            try:
                reader_candidates, provider = reader(image_variants)
                if reader_candidates:
                    candidates.extend(reader_candidates)
                    break
            except Exception as exc:  # pragma: no cover - runtime dependency path
                logger.warning("ocr_reader engine_failed engine=%s error=%s", reader_name, exc)
                if reader_name == "easyocr":
                    warnings.append("EASYOCR_NOT_AVAILABLE")
                elif reader_name == "rapidocr":
                    warnings.append("RAPIDOCR_NOT_AVAILABLE")
                else:
                    warnings.append("PADDLEOCR_NOT_AVAILABLE")

        if not candidates:
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

    def _read_with_rapidocr(self, image_variants: list[tuple[str, Any]]) -> tuple[list[PlateTextCandidate], str]:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore

        engine = RapidOCR()
        candidates: list[PlateTextCandidate] = []
        for _, variant in image_variants:
            result, _ = engine(variant)
            for item in result or []:
                if len(item) < 3:
                    continue
                _, text, confidence = item
                candidates.append(
                    PlateTextCandidate(
                        text=str(text),
                        confidence=float(confidence or 0.0),
                    )
                )
        return candidates, "rapidocr"

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
