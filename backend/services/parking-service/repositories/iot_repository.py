class IoTRepository:
    def open_gate(self, gate_id: str, plate_text: str) -> dict:
        del plate_text
        return {
            "gate_id": gate_id,
            "command": "open",
            "published": True,
        }
