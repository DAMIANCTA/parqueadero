from services.deterministic_face_provider import DeterministicFaceProvider


class MockFaceProvider(DeterministicFaceProvider):
    def __init__(self) -> None:
        super().__init__(model_name="mock-face-model")
