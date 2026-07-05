class MockRepository:
    def get_payload(self) -> dict:
        return {
            "plate": "ABC1234",
            "status": "authorized",
            "authorized_people": 2,
        }
