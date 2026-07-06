import mimetypes
from pathlib import PurePosixPath
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from config import settings
from services.image_payload import LoadedImagePayload


class MinioRepository:
    def __init__(self) -> None:
        parsed = urlparse(settings.minio_internal_url)
        endpoint = parsed.netloc or parsed.path
        secure = parsed.scheme == "https"
        self.client = Minio(
            endpoint,
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=secure,
        )

    def get_object_bytes(self, *, bucket: str, object_name: str) -> bytes:
        response = self.client.get_object(bucket, object_name)
        try:
            return response.read()
        except S3Error:
            raise
        finally:
            response.close()
            response.release_conn()

    def load_registered_image(self, *, image_id: str, bucket: str, object_name: str) -> LoadedImagePayload:
        payload = self.get_object_bytes(bucket=bucket, object_name=object_name)
        guessed_content_type, _ = mimetypes.guess_type(object_name)
        filename = PurePosixPath(object_name).name or "minio-object.bin"
        return LoadedImagePayload(
            image_id=image_id,
            filename=filename,
            content_type=guessed_content_type or "application/octet-stream",
            content=payload,
            source="minio",
            object_name=object_name,
        )
