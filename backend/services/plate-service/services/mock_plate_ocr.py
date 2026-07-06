from repositories.mock_repository import MockRepository
from services.ocr_reader import OcrReader
from services.plate_models import DetectionCandidate, OcrCandidate, PlateImage, PlateTextCandidate


class MockPlateOcr(OcrReader):
    def __init__(self) -> None:
        self.repository = MockRepository()

    def read(self, image: PlateImage, detection: DetectionCandidate) -> OcrCandidate:
        del detection
        payload = self.repository.get_detection_payload(image.filename, image.text_preview)
        return OcrCandidate(
            text=payload["plate_text"],
            confidence=payload["confidence"],
            provider="mock-ocr",
            candidates=[
                PlateTextCandidate(text=item["text"], confidence=item["confidence"])
                for item in payload["candidates"]
            ],
        )
