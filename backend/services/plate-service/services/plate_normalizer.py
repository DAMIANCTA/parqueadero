import re


class PlateNormalizer:
    def normalize(self, plate_text: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9]", "", plate_text or "")
        return cleaned.upper()
