from uuid import UUID

from psycopg import connect
from psycopg.rows import dict_row

from config import settings


class EvidenceReferenceRepository:
    def get_reference(self, image_id: str) -> dict | None:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        COALESCE(bucket, minio_bucket) AS bucket,
                        COALESCE(object_name, object_path) AS object_name,
                        plate,
                        image_type,
                        status
                    FROM image_evidence
                    WHERE id = %(image_id)s
                    """,
                    {"image_id": UUID(image_id)},
                )
                row = cursor.fetchone()
        return None if row is None else dict(row)

    def _connect(self):
        return connect(
            host=settings.postgres_biometrics_host,
            port=settings.postgres_biometrics_internal_port,
            dbname=settings.postgres_biometrics_db,
            user=settings.postgres_biometrics_user,
            password=settings.postgres_biometrics_password,
            connect_timeout=3,
        )
