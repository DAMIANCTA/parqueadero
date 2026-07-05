from abc import ABC, abstractmethod

from services.face_models import ImageReference, LivenessResult


class LivenessProvider(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def check(
        self,
        *,
        image_reference: ImageReference,
        threshold: float,
        challenge_type: str | None = None,
    ) -> LivenessResult:
        raise NotImplementedError
