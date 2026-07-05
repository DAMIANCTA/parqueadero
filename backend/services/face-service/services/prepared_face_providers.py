from services.deterministic_face_provider import DeterministicFaceProvider


class InsightFacePreparedProvider(DeterministicFaceProvider):
    def __init__(self) -> None:
        super().__init__(model_name="insightface-prepared")


class DeepFacePreparedProvider(DeterministicFaceProvider):
    def __init__(self) -> None:
        super().__init__(model_name="deepface-prepared")


class CompreFacePreparedProvider(DeterministicFaceProvider):
    def __init__(self) -> None:
        super().__init__(model_name="compreface-prepared")
