from services.face_models import ImageReference, LivenessResult
from services.liveness_provider import LivenessProvider


class PreparedLivenessProvider(LivenessProvider):
    @property
    def model_name(self) -> str:
        return "prepared-liveness-model"

    def check(
        self,
        *,
        image_reference: ImageReference,
        threshold: float,
        challenge_type: str | None = None,
    ) -> LivenessResult:
        score = 0.88
        lowered = image_reference.object_path.lower()
        if challenge_type and challenge_type.lower() not in {"blink", "look_left", "look_right"}:
            score = 0.7
        if any(flag in lowered for flag in ("spoof", "photo", "replay")):
            score = 0.28
        return LivenessResult(
            passed=score >= threshold,
            score=score,
            threshold=threshold,
            model_name=self.model_name,
        )
