from io import BytesIO
import logging
from math import exp

from config import settings
from services.plate_models import ImageQualityResult


logger = logging.getLogger(__name__)


class ImageQualityService:
    def evaluate(self, image_bytes: bytes) -> ImageQualityResult:
        warnings: list[str] = []
        width = 0
        height = 0
        quality_score = 0.0

        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore

            buffer = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
            if image is None:
                return ImageQualityResult(width=0, height=0, quality_score=0.0, warnings=["INVALID_IMAGE"])

            height, width = image.shape[:2]
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            brightness = float(gray.mean()) / 255.0
            resolution_score = min(1.0, (width * height) / float(settings.plate_quality_min_width * settings.plate_quality_min_height))
            sharpness_score = min(1.0, blur_variance / 180.0)
            brightness_score = exp(-abs(brightness - 0.55) * 2.5)
            quality_score = max(0.0, min(1.0, (resolution_score * 0.4) + (sharpness_score * 0.4) + (brightness_score * 0.2)))
        except Exception:
            try:
                from PIL import Image  # type: ignore

                with Image.open(BytesIO(image_bytes)) as image:
                    width, height = image.size
                resolution_score = min(1.0, (width * height) / float(settings.plate_quality_min_width * settings.plate_quality_min_height))
                quality_score = max(0.0, min(1.0, resolution_score))
                warnings.append("OPENCV_NOT_AVAILABLE")
                logger.warning("image_quality fallback_to_pillow reason=opencv_not_available")
            except Exception:
                logger.exception("image_quality invalid_image unable_to_decode")
                return ImageQualityResult(width=0, height=0, quality_score=0.0, warnings=["INVALID_IMAGE"])

        if width < settings.plate_quality_min_width or height < settings.plate_quality_min_height:
            warnings.append("LOW_RESOLUTION_IMAGE")
        if quality_score < settings.plate_quality_min_score:
            warnings.append("LOW_QUALITY_IMAGE")

        return ImageQualityResult(
            width=width,
            height=height,
            quality_score=round(quality_score, 4),
            warnings=warnings,
        )
