from services.plate_detector import PlateDetector
from services.plate_models import DetectionCandidate, PlateImage


class YoloPreparedPlateDetector(PlateDetector):
    """Lightweight placeholder for a future YOLO detector."""

    def detect(self, image: PlateImage) -> DetectionCandidate:
        base_width = max(160, min(320, len(image.content) // 2 or 180))
        base_height = max(48, min(120, base_width // 3))
        return DetectionCandidate(
            x=64,
            y=128,
            width=base_width,
            height=base_height,
            confidence=0.83,
            provider="yolo-prepared",
        )
