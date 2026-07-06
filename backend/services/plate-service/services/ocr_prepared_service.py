import re

from services.ocr_reader import OcrReader
from services.plate_models import DetectionCandidate, OcrCandidate, PlateImage, PlateTextCandidate


class OcrPreparedService(OcrReader):
    """Placeholder for a future OCR engine."""

    def read(self, image: PlateImage, detection: DetectionCandidate) -> OcrCandidate:
        del detection
        source = f"{image.filename} {image.text_preview}".upper()
        match = re.search(r"[A-Z0-9]{3}[- ]?\d{3,4}", source)
        text = match.group(0).replace("-", "").replace(" ", "") if match else "AGH430"
        return OcrCandidate(
            text=text,
            confidence=0.84,
            provider="ocr-prepared",
            candidates=[
                PlateTextCandidate(text=text, confidence=0.84),
                PlateTextCandidate(text=text.replace("G", "6", 1), confidence=0.66),
            ],
        )
