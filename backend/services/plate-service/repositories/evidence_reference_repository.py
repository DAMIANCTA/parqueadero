import logging
from time import sleep
from uuid import UUID

from psycopg import OperationalError, connect
from psycopg.rows import dict_row

from config import settings


logger = logging.getLogger(__name__)


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
        last_error: OperationalError | None = None
        for attempt in range(1, 4):
            try:
                return connect(
                    host=settings.postgres_biometrics_host,
                    port=settings.postgres_biometrics_internal_port,
                    dbname=settings.postgres_biometrics_db,
                    user=settings.postgres_biometrics_user,
                    password=settings.postgres_biometrics_password,
                    connect_timeout=3,
                )
            except OperationalError as exc:
                last_error = exc
                logger.warning(
                    "evidence_reference_repository connection_failed attempt=%s host=%s port=%s db=%s error=%s",
                    attempt,
                    settings.postgres_biometrics_host,
                    settings.postgres_biometrics_internal_port,
                    settings.postgres_biometrics_db,
                    exc,
                )
                if attempt < 3:
                    sleep(0.5)
        assert last_error is not None
        raise last_error
