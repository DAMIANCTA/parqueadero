from repositories.mock_repository import MockRepository
from services.plate_detector import PlateDetector
from services.plate_models import DetectionCandidate, PlateImage


class MockPlateDetector(PlateDetector):
    def __init__(self) -> None:
        self.repository = MockRepository()

    def detect(self, image: PlateImage) -> DetectionCandidate:
        payload = self.repository.get_detection_payload(image.filename, image.text_preview)
        return DetectionCandidate(
            x=payload["bounding_box"]["x"],
            y=payload["bounding_box"]["y"],
            width=payload["bounding_box"]["width"],
            height=payload["bounding_box"]["height"],
            confidence=payload["confidence"],
            provider="mock-detector",
        )
