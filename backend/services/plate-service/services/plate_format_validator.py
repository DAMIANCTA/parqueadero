import re


class PlateFormatValidator:
    _pattern = re.compile(r"^[A-Z]{3}\d{3,4}$")

    def is_valid(self, plate_text: str) -> bool:
        return bool(self._pattern.fullmatch(plate_text))
