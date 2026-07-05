import re


class PlateFormatValidator:
    _patterns = (
        re.compile(r"^[A-Z]{3}\d{3,4}$"),
        re.compile(r"^[A-Z]{2,4}\d{2,4}$"),
    )

    def is_valid(self, plate_text: str) -> bool:
        return any(pattern.fullmatch(plate_text) for pattern in self._patterns)
