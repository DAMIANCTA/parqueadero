from repositories.mock_repository import MockRepository
from services.plate_models import DetectionCandidate, OcrCandidate, PlateImage
from services.plate_ocr import PlateOcr


class MockPlateOcr(PlateOcr):
    def __init__(self) -> None:
        self.repository = MockRepository()

    def read(self, image: PlateImage, detection: DetectionCandidate) -> OcrCandidate:
        del detection
        payload = self.repository.get_detection_payload(image.filename, image.text_preview)
        return OcrCandidate(
            text=payload["plate_text"],
            confidence=payload["confidence"],
            provider="mock-ocr",
        )
