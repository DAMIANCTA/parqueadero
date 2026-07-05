from abc import ABC, abstractmethod

from services.plate_models import DetectionCandidate, PlateImage


class PlateDetector(ABC):
    @abstractmethod
    def detect(self, image: PlateImage) -> DetectionCandidate:
        raise NotImplementedError
