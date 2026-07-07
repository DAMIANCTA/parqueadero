from typing import Any

from services.plate_models import DetectionCandidate


class PlateCropper:
    def crop(self, image_bgr: Any, detection: DetectionCandidate | None) -> Any | None:
        if image_bgr is None or detection is None:
            return None

        height, width = image_bgr.shape[:2]
        x1 = max(0, detection.x)
        y1 = max(0, detection.y)
        x2 = min(width, detection.x + detection.width)
        y2 = min(height, detection.y + detection.height)
        if x2 <= x1 or y2 <= y1:
            return None
        return image_bgr[y1:y2, x1:x2].copy()
