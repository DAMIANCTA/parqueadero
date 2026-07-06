from dataclasses import dataclass, field


@dataclass(slots=True)
class PlateImage:
    image_id: str
    filename: str
    content_type: str
    content: bytes
    country_code: str
    source: str
    object_name: str | None = None

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
class PlateTextCandidate:
    text: str
    confidence: float


@dataclass(slots=True)
class OcrCandidate:
    text: str
    confidence: float
    provider: str
    candidates: list[PlateTextCandidate] = field(default_factory=list)
