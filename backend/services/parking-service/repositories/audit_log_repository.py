import json
import logging
from time import sleep
from uuid import UUID

from psycopg import OperationalError, connect
from psycopg.rows import dict_row

from config import settings


logger = logging.getLogger(__name__)


class AuditLogRepository:
    def create_entry_audit_log(
        self,
        university_id: str,
        action: str,
        resource_id: str | None,
        metadata: dict,
    ) -> dict:
        return self._create(university_id, action, resource_id, metadata)

    def create_exit_audit_log(
        self,
        university_id: str,
        action: str,
        resource_id: str | None,
        metadata: dict,
    ) -> dict:
        return self._create(university_id, action, resource_id, metadata)

    def _create(self, university_id: str, action: str, resource_id: str | None, metadata: dict) -> dict:
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO audit_logs (id, university_id, action, resource_type, resource_id, metadata)
                    VALUES (gen_random_uuid(), %(university_id)s, %(action)s, 'parking_session', %(resource_id)s, %(metadata)s)
                    RETURNING id
                    """,
                    {
                        "university_id": UUID(university_id),
                        "action": action,
                        "resource_id": UUID(resource_id) if resource_id else None,
                        "metadata": json.dumps(metadata, default=str),
                    },
                )
                row = cursor.fetchone()
            connection.commit()
        return {
            "id": str(row["id"]),
            "university_id": university_id,
            "action": action,
            "resource_id": resource_id,
            "metadata": metadata,
        }

    def _connect(self):
        last_error: OperationalError | None = None
        for attempt in range(1, 4):
            try:
                return connect(
                    host=settings.postgres_core_host,
                    port=settings.postgres_core_internal_port,
                    dbname=settings.postgres_core_db,
                    user=settings.postgres_core_user,
                    password=settings.postgres_core_password,
                    connect_timeout=3,
                )
            except OperationalError as exc:
                last_error = exc
                logger.warning(
                    "audit_log_repository connection_failed attempt=%s host=%s port=%s db=%s error=%s",
                    attempt,
                    settings.postgres_core_host,
                    settings.postgres_core_internal_port,
                    settings.postgres_core_db,
                    exc,
                )
                if attempt < 3:
                    sleep(0.5)
        assert last_error is not None
        raise last_error
