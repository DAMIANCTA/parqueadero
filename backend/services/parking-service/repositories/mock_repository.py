class MockRepository:
    def get_payload(self) -> dict:
        return {
            "session_id": "session-mock-001",
            "session_status": "open",
            "payment_required": True,
        }
