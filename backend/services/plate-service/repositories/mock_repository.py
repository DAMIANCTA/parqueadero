import re


class MockRepository:
    def get_payload(self) -> dict:
        payload = self.get_detection_payload("ABC1234.jpg", "SIMULATED_IMAGE_PLATE=ABC1234")
        return {
            "plate": payload["plate_text"],
            "country_code": "EC",
            "confidence": payload["confidence"],
            "bounding_box": payload["bounding_box"],
            "candidates": payload["candidates"],
        }

    def get_detection_payload(self, filename: str, text_preview: str) -> dict:
        source = f"{filename} {text_preview}".upper()
        if "NO_PLATE" in source or "UNREADABLE" in source:
            return {
                "plate_text": "",
                "confidence": 0.0,
                "bounding_box": {
                    "x": 100,
                    "y": 180,
                    "width": 260,
                    "height": 80,
                },
                "candidates": [],
            }

        match = re.search(r"[A-Z0-9]{3}[- ]?\d{3,4}", source)
        plate_text = (match.group(0) if match else self._fallback_plate(source)).replace("-", "").replace(" ", "")
        primary_confidence = 0.91 if match else 0.84
        secondary = self._secondary_candidate(plate_text)
        candidates = [{"text": plate_text, "confidence": primary_confidence}]
        if secondary != plate_text:
            candidates.append({"text": secondary, "confidence": max(0.55, primary_confidence - 0.19)})
        return {
            "plate_text": plate_text,
            "confidence": primary_confidence,
            "bounding_box": {
                "x": 120,
                "y": 210,
                "width": 260,
                "height": 80,
            },
            "candidates": candidates,
        }

    def _fallback_plate(self, source: str) -> str:
        if "EXIT" in source:
            return "VIS1234"
        if "STUDENT" in source:
            return "ABC1234"
        if "TEACHER" in source:
            return "XYZ9876"
        if "EMPLOYEE" in source:
            return "EMP2026"
        return "AGH430"

    def _secondary_candidate(self, plate_text: str) -> str:
        if len(plate_text) < 4:
            return plate_text
        first_digits = plate_text[:3]
        suffix = plate_text[3:]
        if suffix.startswith("0"):
            suffix = f"O{suffix[1:]}"
        elif suffix.startswith("6"):
            suffix = f"G{suffix[1:]}"
        else:
            suffix = f"6{suffix[1:]}" if suffix else suffix
        return f"{first_digits}{suffix}"
