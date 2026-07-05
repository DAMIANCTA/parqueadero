from abc import ABC, abstractmethod

from services.face_models import FaceEmbedding, ImageReference


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_embedding(
        self,
        *,
        image_reference: ImageReference,
        person_id: str | None = None,
        quality_score_hint: float | None = None,
    ) -> FaceEmbedding:
        raise NotImplementedError
