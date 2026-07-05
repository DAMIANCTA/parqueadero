class MockRepository:
    def get_payload(self) -> dict:
        return {
            "gate_id": "NORTE",
            "command": "open",
            "published": True,
        }
