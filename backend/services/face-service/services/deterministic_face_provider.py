import hashlib

from config import settings
from services.embedding_provider import EmbeddingProvider
from services.face_models import FaceAnalysisResult, FaceBoundingBox, FaceEmbedding, ImageReference
from services.subject_hint import derive_subject_hint


class DeterministicFaceProvider(EmbeddingProvider):
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_embedding(
        self,
        *,
        image_reference: ImageReference,
        person_id: str | None = None,
        quality_score_hint: float | None = None,
    ) -> FaceEmbedding:
        hint = derive_subject_hint(image_reference.object_path, person_id)
        digest = hashlib.sha256(f"{self.model_name}:{hint}".encode("utf-8")).digest()
        vector = [
            round(((digest[index % len(digest)] - 128) / 128), 6)
            for index in range(settings.face_embedding_dimensions)
        ]
        quality_score = quality_score_hint if quality_score_hint is not None else self._estimate_quality(image_reference)
        return FaceEmbedding(
            vector=vector,
            model_name=self.model_name,
            quality_score=max(0.0, min(1.0, round(quality_score, 4))),
        )

    def analyze_face(
        self,
        *,
        image_reference: ImageReference,
        image_bytes: bytes,
        person_id: str | None = None,
        quality_score_hint: float | None = None,
    ) -> FaceAnalysisResult:
        del image_bytes
        embedding = self.generate_embedding(
            image_reference=image_reference,
            person_id=person_id,
            quality_score_hint=quality_score_hint,
        )
        return FaceAnalysisResult(
            detected=True,
            embedding=embedding,
            bounding_box=FaceBoundingBox(x=0, y=0, width=0, height=0),
            provider_name=self.model_name,
            mode_used="prepared",
            warnings=["DETERMINISTIC_FALLBACK_USED"],
        )

    def _estimate_quality(self, image_reference: ImageReference) -> float:
        source = image_reference.object_path.lower()
        if any(flag in source for flag in ("blur", "dark", "noisy")):
            return 0.72
        return 0.93
