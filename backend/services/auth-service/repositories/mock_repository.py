class MockRepository:
    def get_payload(self) -> dict:
        return {
            "strategy": "jwt-mock",
            "sample_user": "gate.operator",
            "sample_role": "gate_operator",
        }
