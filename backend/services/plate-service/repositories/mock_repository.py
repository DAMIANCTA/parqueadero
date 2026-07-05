class MockRepository:
    def get_payload(self) -> dict:
        return {
            "plate": "ABC1234",
            "country_code": "EC",
            "confidence": 0.97,
        }
