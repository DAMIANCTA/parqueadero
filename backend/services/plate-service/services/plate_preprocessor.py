from typing import Any

from config import settings


class PlatePreprocessor:
    def create_variants(self, image_bgr: Any) -> list[tuple[str, Any]]:
        if image_bgr is None:
            return []

        try:
            import cv2  # type: ignore

            working = image_bgr
            _, width = working.shape[:2]
            if width > 0 and width > settings.plate_preprocess_max_width:
                scale = settings.plate_preprocess_max_width / width
                working = cv2.resize(
                    working,
                    None,
                    fx=scale,
                    fy=scale,
                    interpolation=cv2.INTER_AREA,
                )

            gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)
            denoised = cv2.bilateralFilter(gray, 5, 50, 50)
            resize_factor = max(settings.plate_preprocess_resize_factor, 1.0)
            resized = cv2.resize(gray, None, fx=resize_factor, fy=resize_factor, interpolation=cv2.INTER_LINEAR)
            resized_denoised = cv2.bilateralFilter(resized, 5, 50, 50)
            _, otsu = cv2.threshold(resized_denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return [
                ("gray", gray),
                ("resized_denoised", resized_denoised),
                ("otsu", otsu),
            ]
        except Exception:
            return [("raw", image_bgr)]
