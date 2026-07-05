import re

from services.plate_models import DetectionCandidate, OcrCandidate, PlateImage
from services.plate_ocr import PlateOcr


class OcrPreparedService(PlateOcr):
    """Placeholder for a future OCR engine."""

    def read(self, image: PlateImage, detection: DetectionCandidate) -> OcrCandidate:
        del detection
        source = f"{image.filename} {image.text_preview}".upper()
        match = re.search(r"[A-Z]{2,4}[- ]?\d{2,4}", source)
        text = match.group(0) if match else "ABC1234"
        return OcrCandidate(
            text=text,
            confidence=0.84,
            provider="ocr-prepared",
        )
