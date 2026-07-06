from dataclasses import dataclass


@dataclass(slots=True)
class LoadedImagePayload:
    image_id: str
    filename: str
    content_type: str
    content: bytes
    source: str
    object_name: str | None = None
