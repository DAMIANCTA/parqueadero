import io
from urllib.parse import urlparse

from minio import Minio

from config import settings


class MinioRepository:
    _ensured_buckets: set[str] = set()

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

    def ensure_default_buckets(self) -> None:
        for bucket in (
            settings.minio_bucket_faces,
            settings.minio_bucket_plates,
            settings.minio_bucket_evidence,
            settings.minio_bucket_temp,
        ):
            self._ensure_bucket(bucket)

    def upload_object(self, *, bucket: str, object_name: str, payload: bytes, content_type: str) -> None:
        self._ensure_bucket(bucket)
        self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(payload),
            length=len(payload),
            content_type=content_type or "application/octet-stream",
        )

    def _ensure_bucket(self, bucket: str) -> None:
        if bucket in self._ensured_buckets:
            return
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)
        self._ensured_buckets.add(bucket)
