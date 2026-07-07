import logging
from pathlib import Path
from threading import Lock
from typing import Any

from config import settings
from services.plate_models import DetectionCandidate, YoloDetectionDebug, YoloDetectionDebugItem


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
            model_names = self._extract_model_names(self._model)
            logger.info(
                "yolo_plate_detector model_loaded path=%s model_exists=%s model_names=%s",
                self.model_path,
                self.has_model,
                model_names,
            )
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

    def detect_plate_region(self, image_bgr: Any) -> tuple[DetectionCandidate | None, list[str], int, YoloDetectionDebug]:
        warnings: list[str] = []
        debug = YoloDetectionDebug(model_exists=self.has_model, model_loaded=self._model is not None)
        if not self.has_model:
            logger.warning("yolo_plate_detector model_missing path=%s", self.model_path)
            return None, ["MODEL_NOT_FOUND"], 0, debug

        try:
            model = self._load_model()
            debug.model_loaded = True
            debug.model_names = self._extract_model_names(model)
        except Exception as exc:
            logger.warning("yolo_plate_detector unavailable path=%s error=%s", self.model_path, exc)
            return None, ["YOLO_NOT_AVAILABLE"], 0, debug

        results = model.predict(
            source=image_bgr,
            verbose=False,
            conf=settings.plate_detector_confidence,
            imgsz=settings.plate_detector_imgsz,
            device=settings.plate_detector_device,
            max_det=settings.plate_detector_max_detections,
        )
        logger.info(
            "yolo_plate_detector predict model_exists=%s model_loaded=%s conf=%.2f imgsz=%s device=%s max_det=%s",
            debug.model_exists,
            debug.model_loaded,
            settings.plate_detector_confidence,
            settings.plate_detector_imgsz,
            settings.plate_detector_device,
            settings.plate_detector_max_detections,
        )
        if not results:
            logger.info("yolo_plate_detector no_results")
            return None, ["PLATE_REGION_NOT_FOUND"], 0, debug

        result = results[0]
        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            logger.info("yolo_plate_detector no_boxes")
            return None, ["PLATE_REGION_NOT_FOUND"], 0, debug

        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = [max(0, int(value)) for value in xyxy]
            confidence = float(box.conf[0].item()) if getattr(box, "conf", None) is not None else 0.0
            class_id = int(box.cls[0].item()) if getattr(box, "cls", None) is not None else None
            class_name = None
            if class_id is not None and class_id < len(debug.model_names):
                class_name = debug.model_names[class_id]
            debug.detections.append(
                YoloDetectionDebugItem(
                    confidence=max(0.0, min(confidence, 1.0)),
                    box={
                        "x": x1,
                        "y": y1,
                        "width": max(1, x2 - x1),
                        "height": max(1, y2 - y1),
                    },
                    class_id=class_id,
                    class_name=class_name,
                )
            )

        logger.info(
            "yolo_plate_detector detections_count=%s confidences=%s boxes=%s",
            len(debug.detections),
            [round(item.confidence, 4) for item in debug.detections],
            [item.box for item in debug.detections],
        )

        box = max(boxes, key=lambda candidate: float(candidate.conf[0].item()) if getattr(candidate, "conf", None) is not None else 0.0)
        xyxy = box.xyxy[0].tolist()
        x1, y1, x2, y2 = [max(0, int(value)) for value in xyxy]
        width = max(1, x2 - x1)
        height = max(1, y2 - y1)
        confidence = float(box.conf[0].item()) if getattr(box, "conf", None) is not None else 0.0
        selected = DetectionCandidate(
            x=x1,
            y=y1,
            width=width,
            height=height,
            confidence=max(0.0, min(confidence, 1.0)),
            provider="yolo",
        )
        logger.info(
            "yolo_plate_detector selected_detection confidence=%.4f box=%s",
            selected.confidence,
            {"x": selected.x, "y": selected.y, "width": selected.width, "height": selected.height},
        )
        return (
            selected,
            warnings,
            len(boxes),
            debug,
        )

    def _extract_model_names(self, model) -> list[str]:
        names = getattr(model, "names", None)
        if isinstance(names, dict):
            return [str(value) for _, value in sorted(names.items(), key=lambda item: item[0])]
        if isinstance(names, list):
            return [str(value) for value in names]
        return []
