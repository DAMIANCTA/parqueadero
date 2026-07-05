import re


class MockRepository:
    def get_payload(self) -> dict:
        payload = self.get_detection_payload("ABC1234.jpg", "SIMULATED_IMAGE_PLATE=ABC1234")
        return {
            "plate": payload["plate_text"],
            "country_code": "EC",
            "confidence": payload["confidence"],
            "bounding_box": payload["bounding_box"],
        }

    def get_detection_payload(self, filename: str, text_preview: str) -> dict:
        source = f"{filename} {text_preview}".upper()
        match = re.search(r"[A-Z]{2,4}[- ]?\d{2,4}", source)
        plate_text = match.group(0) if match else "ABC1234"
        return {
            "plate_text": plate_text,
            "confidence": 0.97,
            "bounding_box": {
                "x": 120,
                "y": 210,
                "width": 260,
                "height": 80,
            },
        }
