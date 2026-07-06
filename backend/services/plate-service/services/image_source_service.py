import mimetypes
from dataclasses import dataclass
from pathlib import PurePosixPath
from uuid import uuid4

from minio.error import S3Error

from repositories.minio_repository import MinioRepository


@dataclass(slots=True)
class LoadedImagePayload:
    image_id: str
    filename: str
    content_type: str
    content: bytes
    source: str


class ImageSourceService:
    def __init__(self) -> None:
        self.minio_repository = MinioRepository()

    def load_from_upload(
        self,
        *,
        filename: str,
        content_type: str,
        content: bytes,
        image_id: str | None = None,
    ) -> LoadedImagePayload:
        return LoadedImagePayload(
            image_id=image_id or str(uuid4()),
            filename=filename or "upload.jpg",
            content_type=content_type or "application/octet-stream",
            content=content,
            source="upload",
        )

    def load_from_minio(
        self,
        *,
        bucket: str,
        object_name: str,
        image_id: str | None = None,
    ) -> LoadedImagePayload:
        payload = self.minio_repository.get_object_bytes(bucket=bucket, object_name=object_name)
        guessed_content_type, _ = mimetypes.guess_type(object_name)
        filename = PurePosixPath(object_name).name or "minio-object.bin"
        return LoadedImagePayload(
            image_id=image_id or str(uuid4()),
            filename=filename,
            content_type=guessed_content_type or "application/octet-stream",
            content=payload,
            source="minio",
        )

    @staticmethod
    def is_missing_object_error(exc: Exception) -> bool:
        return isinstance(exc, S3Error) and exc.code in {"NoSuchBucket", "NoSuchKey", "NoSuchObject"}
