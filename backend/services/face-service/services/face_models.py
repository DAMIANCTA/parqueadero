from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ImageReference:
    bucket: str
    object_path: str
    object_version: str | None
    sha256_hash: str | None
    content_type: str
    image_type: str

    @property
    def canonical_id(self) -> str:
        return f"{self.bucket}/{self.object_path}"


@dataclass(slots=True)
class FaceEmbedding:
    vector: list[float]
    model_name: str
    quality_score: float


@dataclass(slots=True)
class FaceBoundingBox:
    x: int
    y: int
    width: int
    height: int


@dataclass(slots=True)
class FaceAnalysisResult:
    detected: bool
    embedding: FaceEmbedding | None
    bounding_box: FaceBoundingBox | None
    provider_name: str
    mode_used: str
    warnings: list[str]


@dataclass(slots=True)
class ComparisonResult:
    match: bool
    score: float
    threshold: float
    model_name: str
    metric: str = "similarity"
    operator: str = "gte"


@dataclass(slots=True)
class LivenessResult:
    passed: bool
    score: float
    threshold: float
    model_name: str


@dataclass(slots=True)
class TemplateRecord:
    template_id: str
    image_evidence_id: str
    university_id: str
    person_id: str
    embedding: FaceEmbedding
    image_reference: ImageReference
    encrypted: bool
    expires_at: datetime | None
