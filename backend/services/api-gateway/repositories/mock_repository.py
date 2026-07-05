class MockRepository:
    def get_payload(self) -> dict:
        return {
            "services": [
                "auth-service",
                "university-service",
                "vehicle-service",
                "parking-service",
                "face-service",
                "plate-service",
                "payment-service",
                "iot-service",
                "audit-service",
            ]
        }
