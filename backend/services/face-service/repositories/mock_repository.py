class MockRepository:
    def get_payload(self) -> dict:
        return {
            "match": True,
            "model_name": "mock-face-model",
            "quality_score": 0.98,
        }
