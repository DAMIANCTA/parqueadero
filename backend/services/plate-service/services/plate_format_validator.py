import re

from config import settings


class PlateFormatValidator:
    def __init__(self) -> None:
        self._pattern = re.compile(settings.plate_pattern_regex)

    def is_valid(self, plate_text: str) -> bool:
        return bool(self._pattern.fullmatch(plate_text))
