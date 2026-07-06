from abc import ABC, abstractmethod

from services.plate_models import DetectionCandidate, OcrCandidate, PlateImage


class OcrReader(ABC):
    @abstractmethod
    def read(self, image: PlateImage, detection: DetectionCandidate) -> OcrCandidate:
        raise NotImplementedError
