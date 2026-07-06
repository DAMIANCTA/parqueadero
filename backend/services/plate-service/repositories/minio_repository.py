from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from config import settings


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
