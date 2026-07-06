from uuid import uuid4

from minio.error import S3Error

from repositories.minio_repository import MinioRepository
from services.image_payload import LoadedImagePayload
from services.minio_client import MinioClientService


class ImageSourceService:
    def __init__(self) -> None:
        self.minio_repository = MinioRepository()
        self.minio_client = MinioClientService()

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
        image_id: str | None = None,
        bucket: str | None = None,
        object_name: str | None = None,
    ) -> LoadedImagePayload:
        if image_id:
            return self.minio_client.download_image_from_minio(image_id)
        if not bucket or not object_name:
            raise LookupError("MinIO reference requires image_id or bucket/object_name")
        return self.minio_repository.load_registered_image(
            image_id=image_id or str(uuid4()),
            bucket=bucket,
            object_name=object_name,
        )

    @staticmethod
    def is_missing_object_error(exc: Exception) -> bool:
        return isinstance(exc, S3Error) and exc.code in {"NoSuchBucket", "NoSuchKey", "NoSuchObject"}
