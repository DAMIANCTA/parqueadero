import hashlib
import logging
from datetime import UTC, datetime
from time import sleep
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL

from psycopg import OperationalError, connect
from psycopg.rows import dict_row

from config import settings
from services.face_models import FaceEmbedding, ImageReference, TemplateRecord


logger = logging.getLogger(__name__)


class BiometricRepository:
    _storage_vector_dimensions = 512
    _templates: dict[str, TemplateRecord] = {}
    _latest_template_by_person: dict[tuple[str, str], str] = {}
    _image_evidence: dict[str, dict] = {}
    _logs: dict[str, dict] = {}

    @classmethod
    def reset(cls) -> None:
        cls._templates = {}
        cls._latest_template_by_person = {}
        cls._image_evidence = {}
        cls._logs = {}

    def create_image_evidence(
        self,
        *,
        university_id: str,
        person_id: str | None,
        image_reference: ImageReference,
        encrypted: bool,
        expires_at: datetime | None,
    ) -> str:
        image_evidence_id = str(uuid4())
        payload = {
            "id": image_evidence_id,
            "university_id": university_id,
            "person_id": person_id,
            "minio_bucket": image_reference.bucket,
            "object_path": image_reference.object_path,
            "object_version": image_reference.object_version,
            "sha256_hash": image_reference.sha256_hash or hashlib.sha256(image_reference.canonical_id.encode("utf-8")).hexdigest(),
            "image_type": self._normalize_image_type(image_reference.image_type),
            "content_type": image_reference.content_type,
            "encrypted": encrypted,
            "expires_at": expires_at,
            "status": "active",
        }

        try:
            with self._connect() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        INSERT INTO image_evidence (
                            id,
                            university_id,
                            person_id,
                            minio_bucket,
                            object_path,
                            object_version,
                            sha256_hash,
                            image_type,
                            content_type,
                            expires_at,
                            encrypted,
                            status
                        )
                        VALUES (
                            %(id)s,
                            %(university_id)s,
                            %(person_id)s,
                            %(minio_bucket)s,
                            %(object_path)s,
                            %(object_version)s,
                            %(sha256_hash)s,
                            %(image_type)s,
                            %(content_type)s,
                            %(expires_at)s,
                            %(encrypted)s,
                            %(status)s
                        )
                        ON CONFLICT (minio_bucket, object_path)
                        DO UPDATE SET
                            object_version = EXCLUDED.object_version,
                            content_type = EXCLUDED.content_type,
                            expires_at = EXCLUDED.expires_at,
                            encrypted = EXCLUDED.encrypted,
                            updated_at = NOW()
                        RETURNING id
                        """,
                        {
                            "id": UUID(image_evidence_id),
                            "university_id": self._uuid_value(university_id),
                            "person_id": self._uuid_value(person_id),
                            "minio_bucket": payload["minio_bucket"],
                            "object_path": payload["object_path"],
                            "object_version": payload["object_version"],
                            "sha256_hash": payload["sha256_hash"],
                            "image_type": payload["image_type"],
                            "content_type": payload["content_type"],
                            "expires_at": expires_at,
                            "encrypted": encrypted,
                            "status": "active",
                        },
                    )
                    row = cursor.fetchone()
                connection.commit()
            stored_id = str(row["id"]) if row else image_evidence_id
            payload["id"] = stored_id
            self._image_evidence[stored_id] = payload
            return stored_id
        except OperationalError as exc:
            logger.warning("face-service biometric_repository image_evidence_db_unavailable error=%s", exc)
            self._image_evidence[image_evidence_id] = payload
            return image_evidence_id

    def get_image_evidence(self, image_evidence_id: str) -> dict | None:
        try:
            with self._connect() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        SELECT
                            id,
                            university_id,
                            person_id,
                            minio_bucket,
                            object_path,
                            object_version,
                            sha256_hash,
                            image_type,
                            content_type,
                            captured_at,
                            expires_at,
                            encrypted,
                            status
                        FROM image_evidence
                        WHERE id = %(id)s
                        """,
                        {"id": UUID(image_evidence_id)},
                    )
                    row = cursor.fetchone()
            if row is None:
                return self._image_evidence.get(image_evidence_id)
            normalized = dict(row)
            normalized["id"] = str(normalized["id"])
            normalized["university_id"] = str(normalized["university_id"])
            normalized["person_id"] = str(normalized["person_id"]) if normalized.get("person_id") else None
            return normalized
        except OperationalError as exc:
            logger.warning("face-service biometric_repository image_evidence_lookup_fallback error=%s", exc)
            return self._image_evidence.get(image_evidence_id)

    def create_face_template(
        self,
        *,
        university_id: str,
        person_id: str,
        image_evidence_id: str,
        image_reference: ImageReference,
        embedding: FaceEmbedding,
        encrypted: bool,
        expires_at: datetime | None,
    ) -> TemplateRecord:
        template_id = str(uuid4())
        record = TemplateRecord(
            template_id=template_id,
            image_evidence_id=image_evidence_id,
            university_id=university_id,
            person_id=person_id,
            embedding=embedding,
            image_reference=image_reference,
            encrypted=encrypted,
            expires_at=expires_at,
        )
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO face_templates (
                            id,
                            university_id,
                            person_id,
                            source_image_evidence_id,
                            embedding_vector,
                            model_name,
                            quality_score,
                            encrypted,
                            expires_at,
                            status
                        )
                        VALUES (
                            %(id)s,
                            %(university_id)s,
                            %(person_id)s,
                            %(source_image_evidence_id)s,
                            %(embedding_vector)s::vector,
                            %(model_name)s,
                            %(quality_score)s,
                            %(encrypted)s,
                            %(expires_at)s,
                            'active'
                        )
                        """,
                        {
                            "id": UUID(template_id),
                            "university_id": self._uuid_value(university_id),
                            "person_id": self._uuid_value(person_id),
                            "source_image_evidence_id": UUID(image_evidence_id),
                            "embedding_vector": self._vector_literal(embedding.vector),
                            "model_name": embedding.model_name,
                            "quality_score": embedding.quality_score,
                            "encrypted": encrypted,
                            "expires_at": expires_at,
                        },
                    )
                connection.commit()
        except OperationalError as exc:
            logger.warning("face-service biometric_repository template_db_unavailable error=%s", exc)
        self._templates[template_id] = record
        self._latest_template_by_person[(university_id, person_id)] = template_id
        return record

    def get_template(self, template_id: str) -> TemplateRecord | None:
        try:
            with self._connect() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        SELECT
                            ft.id,
                            ft.university_id,
                            ft.person_id,
                            ft.source_image_evidence_id,
                            ft.embedding_vector::text AS embedding_vector,
                            ft.model_name,
                            ft.quality_score,
                            ft.encrypted,
                            ft.expires_at,
                            ie.minio_bucket,
                            ie.object_path,
                            ie.object_version,
                            ie.sha256_hash,
                            ie.content_type,
                            ie.image_type
                        FROM face_templates ft
                        LEFT JOIN image_evidence ie ON ie.id = ft.source_image_evidence_id
                        WHERE ft.id = %(id)s
                        ORDER BY ft.created_at DESC
                        LIMIT 1
                        """,
                        {"id": UUID(template_id)},
                    )
                    row = cursor.fetchone()
            if row:
                return self._row_to_template(row)
        except OperationalError as exc:
            logger.warning("face-service biometric_repository template_lookup_fallback error=%s", exc)
        return self._templates.get(template_id)

    def get_latest_template(self, university_id: str, person_id: str) -> TemplateRecord | None:
        try:
            with self._connect() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        SELECT
                            ft.id,
                            ft.university_id,
                            ft.person_id,
                            ft.source_image_evidence_id,
                            ft.embedding_vector::text AS embedding_vector,
                            ft.model_name,
                            ft.quality_score,
                            ft.encrypted,
                            ft.expires_at,
                            ie.minio_bucket,
                            ie.object_path,
                            ie.object_version,
                            ie.sha256_hash,
                            ie.content_type,
                            ie.image_type
                        FROM face_templates ft
                        LEFT JOIN image_evidence ie ON ie.id = ft.source_image_evidence_id
                        WHERE ft.university_id = %(university_id)s
                          AND ft.person_id = %(person_id)s
                        ORDER BY ft.created_at DESC
                        LIMIT 1
                        """,
                        {
                            "university_id": self._uuid_value(university_id),
                            "person_id": self._uuid_value(person_id),
                        },
                    )
                    row = cursor.fetchone()
            if row:
                return self._row_to_template(row)
        except OperationalError as exc:
            logger.warning("face-service biometric_repository latest_template_lookup_fallback error=%s", exc)

        template_id = self._latest_template_by_person.get((university_id, person_id))
        if not template_id:
            return None
        return self._templates.get(template_id)

    def create_biometric_log(
        self,
        *,
        university_id: str | None,
        person_id: str | None,
        template_id: str | None,
        image_evidence_id: str,
        operation_type: str,
        model_name: str,
        similarity_score: float | None,
        quality_score: float | None,
        liveness_score: float | None,
        decision: str,
        metadata: dict | None = None,
        session_reference_id: str | None = None,
        gate_reference_id: str | None = None,
    ) -> str:
        log_id = str(uuid4())
        payload = {
            "id": log_id,
            "university_id": university_id,
            "person_id": person_id,
            "face_template_id": template_id,
            "image_evidence_id": image_evidence_id,
            "operation_type": self._normalize_operation_type(operation_type),
            "model_name": model_name,
            "similarity_score": similarity_score,
            "quality_score": quality_score,
            "liveness_score": liveness_score,
            "decision": self._normalize_decision(decision),
            "metadata": metadata or {},
            "session_reference_id": session_reference_id,
            "gate_reference_id": gate_reference_id,
            "occurred_at": datetime.now(UTC).isoformat(),
            "status": "active",
        }
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO biometric_access_logs (
                            id,
                            university_id,
                            person_id,
                            face_template_id,
                            image_evidence_id,
                            session_reference_id,
                            gate_reference_id,
                            operation_type,
                            model_name,
                            similarity_score,
                            quality_score,
                            liveness_score,
                            decision,
                            metadata,
                            status
                        )
                        VALUES (
                            %(id)s,
                            %(university_id)s,
                            %(person_id)s,
                            %(face_template_id)s,
                            %(image_evidence_id)s,
                            %(session_reference_id)s,
                            %(gate_reference_id)s,
                            %(operation_type)s,
                            %(model_name)s,
                            %(similarity_score)s,
                            %(quality_score)s,
                            %(liveness_score)s,
                            %(decision)s,
                            %(metadata)s::jsonb,
                            'active'
                        )
                        """,
                        {
                            "id": UUID(log_id),
                            "university_id": self._uuid_value(university_id),
                            "person_id": self._uuid_value(person_id),
                            "face_template_id": UUID(template_id) if template_id else None,
                            "image_evidence_id": UUID(image_evidence_id),
                            "session_reference_id": self._uuid_value(session_reference_id),
                            "gate_reference_id": self._uuid_value(gate_reference_id),
                            "operation_type": payload["operation_type"],
                            "model_name": model_name,
                            "similarity_score": similarity_score,
                            "quality_score": quality_score,
                            "liveness_score": liveness_score,
                            "decision": payload["decision"],
                            "metadata": self._json_dump(payload["metadata"]),
                        },
                    )
                connection.commit()
        except OperationalError as exc:
            logger.warning("face-service biometric_repository biometric_log_db_unavailable error=%s", exc)
        self._logs[log_id] = payload
        return log_id

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
                    "face-service biometric_repository connection_failed attempt=%s host=%s port=%s db=%s error=%s",
                    attempt,
                    settings.postgres_biometrics_host,
                    settings.postgres_biometrics_internal_port,
                    settings.postgres_biometrics_db,
                    exc,
                )
                if attempt < 3:
                    sleep(0.3)
        assert last_error is not None
        raise last_error

    def _row_to_template(self, row: dict) -> TemplateRecord:
        return TemplateRecord(
            template_id=str(row["id"]),
            image_evidence_id=str(row["source_image_evidence_id"]),
            university_id=str(row["university_id"]),
            person_id=str(row["person_id"]),
            embedding=FaceEmbedding(
                vector=self._parse_vector(str(row["embedding_vector"])),
                model_name=row["model_name"],
                quality_score=float(row["quality_score"]) if row.get("quality_score") is not None else 0.0,
            ),
            image_reference=ImageReference(
                bucket=row.get("minio_bucket") or settings.face_default_bucket,
                object_path=row.get("object_path") or "",
                object_version=row.get("object_version"),
                sha256_hash=row.get("sha256_hash"),
                content_type=row.get("content_type") or "image/jpeg",
                image_type=row.get("image_type") or "face_capture",
            ),
            encrypted=bool(row.get("encrypted", True)),
            expires_at=row.get("expires_at"),
        )

    def _normalize_operation_type(self, value: str) -> str:
        mapping = {
            "enroll": "enrollment",
            "verify": "revalidation",
            "compare": "revalidation",
            "detect": "entry_validation",
            "entry_validation": "entry_validation",
            "exit_validation": "exit_validation",
            "liveness": "manual_review",
            "liveness_check": "manual_review",
        }
        return mapping.get(value, "manual_review")

    def _normalize_decision(self, value: str) -> str:
        mapping = {
            "match": "approved",
            "passed": "approved",
            "approved": "approved",
            "no_match": "rejected",
            "failed": "rejected",
            "rejected": "rejected",
            "manual_review": "manual_review",
            "error": "error",
        }
        return mapping.get(value, "manual_review")

    def _normalize_image_type(self, image_type: str) -> str:
        if image_type in {"face_entry", "face_exit"}:
            return image_type
        if image_type in {"face_enroll", "face_enrollment"}:
            return "face_enrollment"
        if image_type == "liveness_frame":
            return "liveness_frame"
        return "other"

    def _uuid_value(self, raw: str | None) -> UUID | None:
        if not raw:
            return None
        try:
            return UUID(str(raw))
        except ValueError:
            return uuid5(NAMESPACE_URL, str(raw))

    def _vector_literal(self, vector: list[float]) -> str:
        storage_vector = list(vector)
        if len(storage_vector) < self._storage_vector_dimensions:
            logger.info(
                "face-service biometric_repository pad_embedding original_dimensions=%s storage_dimensions=%s",
                len(storage_vector),
                self._storage_vector_dimensions,
            )
            storage_vector = storage_vector + [0.0] * (self._storage_vector_dimensions - len(storage_vector))
        elif len(storage_vector) > self._storage_vector_dimensions:
            logger.warning(
                "face-service biometric_repository truncate_embedding original_dimensions=%s storage_dimensions=%s",
                len(storage_vector),
                self._storage_vector_dimensions,
            )
            storage_vector = storage_vector[: self._storage_vector_dimensions]
        return "[" + ",".join(str(round(float(value), 6)) for value in storage_vector) + "]"

    def _parse_vector(self, raw: str) -> list[float]:
        cleaned = raw.strip().strip("[]")
        if not cleaned:
            return []
        return [float(value) for value in cleaned.split(",")]

    def _json_dump(self, payload: dict) -> str:
        import json

        return json.dumps(payload, separators=(",", ":"), sort_keys=True)
