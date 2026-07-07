from pathlib import Path
from typing import Any

from config import settings
from services.plate_models import DetectionCandidate


class YoloPlateDetectorService:
    def __init__(self) -> None:
        self.model_path = Path(__file__).resolve().parent.parent / settings.plate_detector_model_path

    @property
    def has_model(self) -> bool:
        return self.model_path.exists()

    def detect_plate_region(self, image_bgr: Any) -> tuple[DetectionCandidate | None, list[str]]:
        warnings: list[str] = []
        if not self.has_model:
            return None, ["MODEL_NOT_FOUND"]

        try:
            from ultralytics import YOLO  # type: ignore
        except Exception:
            return None, ["YOLO_NOT_AVAILABLE"]

        model = YOLO(str(self.model_path))
        results = model.predict(source=image_bgr, verbose=False, conf=0.15)
        if not results:
            return None, ["PLATE_REGION_NOT_FOUND"]

        result = results[0]
        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            return None, ["PLATE_REGION_NOT_FOUND"]

        box = boxes[0]
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
        )
