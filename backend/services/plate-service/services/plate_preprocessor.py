from typing import Any


class PlatePreprocessor:
    def create_variants(self, image_bgr: Any) -> list[tuple[str, Any]]:
        if image_bgr is None:
            return []

        try:
            import cv2  # type: ignore

            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            denoised = cv2.bilateralFilter(gray, 7, 50, 50)
            equalized = cv2.equalizeHist(denoised)
            adaptive = cv2.adaptiveThreshold(
                equalized,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                11,
            )
            _, otsu = cv2.threshold(equalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return [
                ("gray", gray),
                ("equalized", equalized),
                ("adaptive", adaptive),
                ("otsu", otsu),
            ]
        except Exception:
            return [("raw", image_bgr)]
