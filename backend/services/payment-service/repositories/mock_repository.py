class MockRepository:
    def get_payload(self) -> dict:
        return {
            "payment_status": "paid",
            "amount": 1.50,
            "currency": "USD",
        }
