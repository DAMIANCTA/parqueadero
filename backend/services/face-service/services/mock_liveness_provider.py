from services.face_models import ImageReference, LivenessResult
from services.liveness_provider import LivenessProvider


class MockLivenessProvider(LivenessProvider):
    @property
    def model_name(self) -> str:
        return "mock-liveness-model"

    def check(
        self,
        *,
        image_reference: ImageReference,
        threshold: float,
        challenge_type: str | None = None,
    ) -> LivenessResult:
        del challenge_type
        score = 0.94
        lowered = image_reference.object_path.lower()
        if any(flag in lowered for flag in ("spoof", "photo", "replay")):
            score = 0.31
        return LivenessResult(
            passed=score >= threshold,
            score=score,
            threshold=threshold,
            model_name=self.model_name,
        )
