import re


class PlateNormalizer:
    _letter_replacements = {
        "0": "O",
        "1": "I",
        "5": "S",
        "6": "G",
        "8": "B",
    }
    _digit_replacements = {
        "O": "0",
        "I": "1",
        "S": "5",
        "B": "8",
        "G": "6",
    }

    def normalize(self, plate_text: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9]", "", plate_text or "").upper()
        if len(cleaned) < 6:
            return cleaned

        letters = "".join(self._letter_replacements.get(char, char) for char in cleaned[:3])
        digits = "".join(self._digit_replacements.get(char, char) for char in cleaned[3:])
        return f"{letters}{digits}"
