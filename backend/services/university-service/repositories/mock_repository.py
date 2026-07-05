class MockRepository:
    def get_payload(self) -> dict:
        return {
            "university_code": "UDSP",
            "campuses": 1,
            "gates": ["Puerta Norte", "Puerta Sur"],
        }
