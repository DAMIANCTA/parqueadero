from dataclasses import dataclass
from pathlib import Path

from config import settings


@dataclass(slots=True)
class RuntimeCapabilities:
    opencv_available: bool
    easyocr_available: bool
    rapidocr_available: bool
    paddleocr_available: bool
    ocr_engine: str
    model_path: str
    model_exists: bool
    plate_detection_mode: str
    plate_service_mode: str
    environment: str
    min_confidence: float
    errors: dict[str, str]


def probe_runtime_capabilities() -> RuntimeCapabilities:
    errors: dict[str, str] = {}

    opencv_available = _module_available("cv2", errors, "opencv")
    easyocr_available = _module_available("easyocr", errors, "easyocr")
    rapidocr_available = _rapidocr_available(errors)
    paddleocr_available = _module_available("paddleocr", errors, "paddleocr")

    resolved_model_path = Path(__file__).resolve().parent.parent / settings.plate_detector_model_path
    model_exists = resolved_model_path.exists()

    ocr_engine = _select_ocr_engine(
        preferred_engine=settings.plate_ocr_preferred_engine,
        easyocr_available=easyocr_available,
        rapidocr_available=rapidocr_available,
        paddleocr_available=paddleocr_available,
    )

    return RuntimeCapabilities(
        opencv_available=opencv_available,
        easyocr_available=easyocr_available,
        rapidocr_available=rapidocr_available,
        paddleocr_available=paddleocr_available,
        ocr_engine=ocr_engine,
        model_path=settings.plate_detector_model_path,
        model_exists=model_exists,
        plate_detection_mode=settings.effective_plate_detection_mode,
        plate_service_mode=settings.plate_service_mode,
        environment=settings.environment,
        min_confidence=settings.plate_min_confidence,
        errors=errors,
    )


def _module_available(module_name: str, errors: dict[str, str], error_key: str) -> bool:
    try:
        __import__(module_name)
        return True
    except Exception as exc:  # pragma: no cover - runtime dependency path
        errors[error_key] = str(exc)
        return False


def _rapidocr_available(errors: dict[str, str]) -> bool:
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore

        _ = RapidOCR
        return True
    except Exception as exc:  # pragma: no cover - runtime dependency path
        errors["rapidocr"] = str(exc)
        return False


def _select_ocr_engine(
    *,
    preferred_engine: str,
    easyocr_available: bool,
    rapidocr_available: bool,
    paddleocr_available: bool,
) -> str:
    preferred = (preferred_engine or "").strip().lower()
    availability = {
        "easyocr": easyocr_available,
        "rapidocr": rapidocr_available,
        "paddleocr": paddleocr_available,
    }
    if availability.get(preferred):
        return preferred

    for engine_name, available in (
        ("easyocr", easyocr_available),
        ("rapidocr", rapidocr_available),
        ("paddleocr", paddleocr_available),
    ):
        if available:
            return engine_name
    return "none"
