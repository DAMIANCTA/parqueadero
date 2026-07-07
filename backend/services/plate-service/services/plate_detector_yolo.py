import logging
from pathlib import Path
from threading import Lock
from typing import Any

from config import settings
from services.plate_models import DetectionCandidate


logger = logging.getLogger(__name__)


class YoloPlateDetectorService:
    def __init__(self) -> None:
        self.model_path = Path(__file__).resolve().parent.parent / settings.plate_detector_model_path
        self._model = None
        self._model_lock = Lock()

    @property
    def has_model(self) -> bool:
        return self.model_path.exists()

    def _load_model(self):
        if self._model is not None:
            return self._model

        with self._model_lock:
            if self._model is not None:
                return self._model

            from ultralytics import YOLO  # type: ignore

            self._model = YOLO(str(self.model_path))
            logger.info("yolo_plate_detector model_loaded path=%s", self.model_path)
            return self._model

    def warm_up(self) -> bool:
        if not self.has_model:
            return False
        try:
            self._load_model()
            return True
        except Exception as exc:
            logger.warning("yolo_plate_detector warmup_failed path=%s error=%s", self.model_path, exc)
            return False

    def detect_plate_region(self, image_bgr: Any) -> tuple[DetectionCandidate | None, list[str], int]:
        warnings: list[str] = []
        if not self.has_model:
            return None, ["MODEL_NOT_FOUND"], 0

        try:
            model = self._load_model()
        except Exception:
            return None, ["YOLO_NOT_AVAILABLE"], 0

        results = model.predict(
            source=image_bgr,
            verbose=False,
            conf=settings.plate_detector_confidence,
            imgsz=settings.plate_detector_imgsz,
            device=settings.plate_detector_device,
            max_det=settings.plate_detector_max_detections,
        )
        if not results:
            return None, ["PLATE_REGION_NOT_FOUND"], 0

        result = results[0]
        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            return None, ["PLATE_REGION_NOT_FOUND"], 0

        box = max(boxes, key=lambda candidate: float(candidate.conf[0].item()) if getattr(candidate, "conf", None) is not None else 0.0)
        xyxy = box.xyxy[0].tolist()
        x1, y1, x2, y2 = [max(0, int(value)) for value in xyxy]
        width = max(1, x2 - x1)
        height = max(1, y2 - y1)
        confidence = float(box.conf[0].item()) if getattr(box, "conf", None) is not None else 0.0
        return (
            DetectionCandidate(
                x=x1,
                y=y1,
                width=width,
                height=height,
                confidence=max(0.0, min(confidence, 1.0)),
                provider="yolo",
            ),
            warnings,
            len(boxes),
        )
