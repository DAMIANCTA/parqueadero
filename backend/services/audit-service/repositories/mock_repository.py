class MockRepository:
    def get_payload(self) -> dict:
        return {
            "resource_type": "parking_session",
            "action": "entry_granted",
            "records": 1,
        }
