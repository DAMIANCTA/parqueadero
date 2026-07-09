from uuid import UUID

from psycopg import OperationalError, connect
from psycopg.rows import dict_row

from config import settings


class BiometricEvidenceRepository:
    def get_image_reference(self, image_id: str) -> dict | None:
        try:
            with connect(
                host=settings.postgres_biometrics_host,
                port=settings.postgres_biometrics_internal_port,
                dbname=settings.postgres_biometrics_db,
                user=settings.postgres_biometrics_user,
                password=settings.postgres_biometrics_password,
                connect_timeout=3,
            ) as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        SELECT
                            id,
                            minio_bucket,
                            object_path,
                            object_version,
                            sha256_hash,
                            content_type,
                            image_type
                        FROM image_evidence
                        WHERE id = %(id)s
                        """,
                        {"id": UUID(str(image_id))},
                    )
                    row = cursor.fetchone()
            if row is None:
                return None
            return {
                "image_id": str(row["id"]),
                "bucket": row["minio_bucket"],
                "object_path": row["object_path"],
                "object_version": row.get("object_version"),
                "sha256_hash": row.get("sha256_hash"),
                "content_type": row.get("content_type") or "image/jpeg",
                "image_type": row.get("image_type") or "face_capture",
            }
        except (OperationalError, ValueError):
            return None

