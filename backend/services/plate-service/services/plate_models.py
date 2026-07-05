from dataclasses import dataclass


@dataclass(slots=True)
class PlateImage:
    filename: str
    content_type: str
    content: bytes
    country_code: str

    @property
    def text_preview(self) -> str:
        return self.content.decode("utf-8", errors="ignore")


@dataclass(slots=True)
class DetectionCandidate:
    x: int
    y: int
    width: int
    height: int
    confidence: float
    provider: str


@dataclass(slots=True)
class OcrCandidate:
    text: str
    confidence: float
    provider: str
