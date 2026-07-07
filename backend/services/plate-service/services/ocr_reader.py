from abc import ABC, abstractmethod
import logging
from threading import Lock
from typing import Any

from config import settings
from services.plate_models import DetectionCandidate, OcrCandidate, PlateImage
from services.plate_models import PlateTextCandidate
from services.runtime_probe import probe_runtime_capabilities


logger = logging.getLogger(__name__)


class OcrReader(ABC):
    @abstractmethod
    def read(self, image: PlateImage, detection: DetectionCandidate) -> OcrCandidate:
        raise NotImplementedError


class OCRReaderService:
    def __init__(self) -> None:
        self._rapidocr_engine = None
        self._easyocr_reader = None
        self._paddleocr_reader = None
        self._engine_lock = Lock()

    def read_plate_text(self, image_variants: list[tuple[str, Any]]) -> tuple[list[PlateTextCandidate], list[str], str, str]:
        warnings: list[str] = []
        candidates: list[PlateTextCandidate] = []
        provider = "none"

        capabilities = probe_runtime_capabilities()
        selected_engine = self._selected_engine(capabilities)
        preferred_engine = (settings.plate_ocr_preferred_engine or "").strip().lower()
        logger.info(
            "ocr_reader selected_engine=%s preferred_engine=%s available_easyocr=%s available_rapidocr=%s available_paddleocr=%s",
            selected_engine,
            preferred_engine,
            capabilities.easyocr_available,
            capabilities.rapidocr_available,
            capabilities.paddleocr_available,
        )

        if selected_engine == "none":
            warnings.extend(self._dependency_warnings(capabilities, preferred_engine))
            warnings.append("OCR_ENGINE_NOT_AVAILABLE")
            return candidates, self._unique(warnings), provider, selected_engine

        try:
            reader_candidates, provider = self._run_selected_engine(selected_engine, image_variants)
            if reader_candidates:
                candidates.extend(reader_candidates)
        except Exception as exc:  # pragma: no cover - runtime dependency path
            logger.warning("ocr_reader engine_failed engine=%s error=%s", selected_engine, exc)
            warnings.append("OCR_ENGINE_FAILED")

        return candidates, self._unique(warnings), provider, selected_engine

    def warm_up(self) -> bool:
        capabilities = probe_runtime_capabilities()
        selected_engine = self._selected_engine(capabilities)
        if selected_engine == "none":
            return False
        try:
            self._get_engine(selected_engine)
            return True
        except Exception as exc:  # pragma: no cover - runtime dependency path
            logger.warning("ocr_reader warmup_failed engine=%s error=%s", selected_engine, exc)
            return False

    def _selected_engine(self, capabilities) -> str:
        preferred_engine = (settings.plate_ocr_preferred_engine or "").strip().lower()
        availability = {
            "easyocr": capabilities.easyocr_available,
            "rapidocr": capabilities.rapidocr_available,
            "paddleocr": capabilities.paddleocr_available,
        }
        if preferred_engine in availability:
            return preferred_engine if availability[preferred_engine] else "none"
        return "none"

    def _dependency_warnings(self, capabilities, preferred_engine: str) -> list[str]:
        engine_warning_map = {
            "easyocr": "EASYOCR_NOT_AVAILABLE",
            "rapidocr": "RAPIDOCR_NOT_AVAILABLE",
            "paddleocr": "PADDLEOCR_NOT_AVAILABLE",
        }
        error = capabilities.errors.get(preferred_engine)
        warning_code = engine_warning_map.get(preferred_engine)
        if warning_code and error:
            logger.warning("ocr_reader dependency_unavailable engine=%s error=%s", preferred_engine, error)
            return [warning_code]
        return []

    def _run_selected_engine(self, selected_engine: str, image_variants: list[tuple[str, Any]]) -> tuple[list[PlateTextCandidate], str]:
        if selected_engine == "easyocr":
            return self._read_with_easyocr(image_variants)
        if selected_engine == "rapidocr":
            return self._read_with_rapidocr(image_variants)
        if selected_engine == "paddleocr":
            return self._read_with_paddleocr(image_variants)
        return [], "none"

    def _get_engine(self, selected_engine: str):
        with self._engine_lock:
            if selected_engine == "rapidocr":
                if self._rapidocr_engine is None:
                    from rapidocr_onnxruntime import RapidOCR  # type: ignore

                    self._rapidocr_engine = RapidOCR()
                return self._rapidocr_engine
            if selected_engine == "easyocr":
                if self._easyocr_reader is None:
                    import easyocr  # type: ignore

                    self._easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
                return self._easyocr_reader
            if selected_engine == "paddleocr":
                if self._paddleocr_reader is None:
                    from paddleocr import PaddleOCR  # type: ignore

                    self._paddleocr_reader = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
                return self._paddleocr_reader
        return None

    def _read_with_easyocr(self, image_variants: list[tuple[str, Any]]) -> tuple[list[PlateTextCandidate], str]:
        reader = self._get_engine("easyocr")
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
        engine = self._get_engine("rapidocr")
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
        ocr = self._get_engine("paddleocr")
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
