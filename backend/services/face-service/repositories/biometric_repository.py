from datetime import datetime
from uuid import uuid4

from services.face_models import FaceEmbedding, ImageReference, TemplateRecord


class BiometricRepository:
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
        self._image_evidence[image_evidence_id] = {
            "id": image_evidence_id,
            "university_id": university_id,
            "person_id": person_id,
            "minio_bucket": image_reference.bucket,
            "object_path": image_reference.object_path,
            "object_version": image_reference.object_version,
            "sha256_hash": image_reference.sha256_hash,
            "image_type": image_reference.image_type,
            "content_type": image_reference.content_type,
            "encrypted": encrypted,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "status": "active",
        }
        return image_evidence_id

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
        self._templates[template_id] = record
        self._latest_template_by_person[(university_id, person_id)] = template_id
        return record

    def get_template(self, template_id: str) -> TemplateRecord | None:
        return self._templates.get(template_id)

    def get_latest_template(self, university_id: str, person_id: str) -> TemplateRecord | None:
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
    ) -> str:
        log_id = str(uuid4())
        self._logs[log_id] = {
            "id": log_id,
            "university_id": university_id,
            "person_id": person_id,
            "face_template_id": template_id,
            "image_evidence_id": image_evidence_id,
            "operation_type": operation_type,
            "model_name": model_name,
            "similarity_score": similarity_score,
            "quality_score": quality_score,
            "liveness_score": liveness_score,
            "decision": decision,
            "metadata": metadata or {},
            "occurred_at": datetime.utcnow().isoformat(),
            "status": "active",
        }
        return log_id
