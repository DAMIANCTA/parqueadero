import logging
from io import BytesIO
from urllib.parse import urlparse

from minio import Minio

from config import settings


logger = logging.getLogger(__name__)


class MinioImageService:
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

    def download_bytes(self, *, bucket: str, object_path: str) -> bytes:
        logger.info("face-service minio_download bucket=%s object_path=%s", bucket, object_path)
        response = self.client.get_object(bucket, object_path)
        try:
            return BytesIO(response.read()).getvalue()
        finally:
            response.close()
            response.release_conn()
