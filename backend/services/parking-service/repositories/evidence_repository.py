import logging
from time import sleep
from typing import Any
from uuid import UUID, uuid4

from psycopg import OperationalError, connect
from psycopg.rows import dict_row

from config import settings


logger = logging.getLogger(__name__)


class EvidenceRepository:
    def create_reference(
        self,
        *,
        bucket: str,
        object_name: str,
        image_type: str,
        plate: str,
        hash_sha256: str,
        university_id: str | None = None,
        content_type: str = "application/octet-stream",
        session_id: str | None = None,
        encrypted: bool = True,
        expires_at: str | None = None,
        status: str = "active",
    ) -> dict:
        image_id = str(uuid4())
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    INSERT INTO image_evidence (
                        id,
                        university_id,
                        person_id,
                        session_id,
                        plate,
                        minio_bucket,
                        bucket,
                        object_path,
                        object_name,
                        object_version,
                        sha256_hash,
                        hash_sha256,
                        image_type,
                        content_type,
                        encrypted,
                        expires_at,
                        status
                    )
                    VALUES (
                        %(image_id)s,
                        %(university_id)s,
                        NULL,
                        %(session_id)s,
                        %(plate)s,
                        %(bucket)s,
                        %(bucket)s,
                        %(object_name)s,
                        %(object_name)s,
                        NULL,
                        %(hash_sha256)s,
                        %(hash_sha256)s,
                        %(image_type)s,
                        %(content_type)s,
                        %(encrypted)s,
                        %(expires_at)s,
                        %(status)s
                    )
                    RETURNING
                        id AS image_id,
                        session_id,
                        plate,
                        bucket,
                        object_name,
                        image_type,
                        hash_sha256,
                        encrypted,
                        created_at,
                        expires_at,
                        status
                    """,
                    {
                        "image_id": image_id,
                        "university_id": UUID(university_id) if university_id else UUID(settings.evidence_default_university_id),
                        "session_id": UUID(session_id) if session_id else None,
                        "plate": plate,
                        "bucket": bucket,
                        "object_name": object_name,
                        "hash_sha256": hash_sha256,
                        "image_type": image_type,
                        "content_type": content_type,
                        "encrypted": encrypted,
                        "expires_at": expires_at,
                        "status": status,
                    },
                )
                row = cursor.fetchone()
            connection.commit()
        return self._normalize_row(row)

    def link_to_session(self, image_id: str, session_id: str, plate: str) -> dict | None:
        try:
            image_uuid = UUID(image_id)
            session_uuid = UUID(session_id)
        except ValueError:
            logger.info(
                "evidence_repository skip_link_non_uuid image_id=%s session_id=%s plate=%s",
                image_id,
                session_id,
                plate,
            )
            return None
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    UPDATE image_evidence
                    SET session_id = %(session_id)s,
                        plate = %(plate)s
                    WHERE id = %(image_id)s
                    RETURNING
                        id AS image_id,
                        session_id,
                        plate,
                        bucket,
                        object_name,
                        image_type,
                        hash_sha256,
                        encrypted,
                        created_at,
                        expires_at,
                        status
                    """,
                    {
                        "image_id": image_uuid,
                        "session_id": session_uuid,
                        "plate": plate,
                    },
                )
                row = cursor.fetchone()
            connection.commit()
        return None if row is None else self._normalize_row(row)

    def get(self, image_id: str) -> dict | None:
        try:
            image_uuid = UUID(image_id)
        except ValueError:
            return None
        with self._connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id AS image_id,
                        session_id,
                        plate,
                        bucket,
                        object_name,
                        image_type,
                        hash_sha256,
                        encrypted,
                        created_at,
                        expires_at,
                        status
                    FROM image_evidence
                    WHERE id = %(image_id)s
                    """,
                    {"image_id": image_uuid},
                )
                row = cursor.fetchone()
        return None if row is None else self._normalize_row(row)

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
                    "evidence_repository connection_failed attempt=%s host=%s port=%s db=%s error=%s",
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

    def _normalize_row(self, row: dict[str, Any]) -> dict:
        normalized = dict(row)
        normalized["image_id"] = str(normalized["image_id"])
        normalized["session_id"] = str(normalized["session_id"]) if normalized.get("session_id") else None
        normalized["created_at"] = normalized["created_at"].isoformat().replace("+00:00", "Z")
        normalized["expires_at"] = (
            normalized["expires_at"].isoformat().replace("+00:00", "Z")
            if normalized.get("expires_at")
            else None
        )
        return normalized
