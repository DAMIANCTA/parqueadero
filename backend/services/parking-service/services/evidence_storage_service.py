import re
from hashlib import sha256
from datetime import datetime, timezone
from uuid import uuid4

from config import settings
from repositories.evidence_repository import EvidenceRepository
from repositories.minio_repository import MinioRepository


class EvidenceStorageService:
    def __init__(self) -> None:
        self.repository = EvidenceRepository()
        self.storage = MinioRepository()

    def upload_evidence(
        self,
        *,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        image_type: str,
        plate: str,
        university_id: str | None = None,
        session_id: str | None = None,
    ) -> dict:
        normalized_plate = plate.strip().upper().replace(" ", "")
        if not normalized_plate:
            raise ValueError("Plate is required")
        if not file_bytes:
            raise ValueError("Evidence file is empty")

        self.storage.ensure_default_buckets()
        bucket = self._resolve_bucket(image_type)
        object_name = self._build_object_name(filename=filename, image_type=image_type, plate=normalized_plate)
        self.storage.upload_object(
            bucket=bucket,
            object_name=object_name,
            payload=file_bytes,
            content_type=content_type,
        )
        hash_sha256 = sha256(file_bytes).hexdigest()
        return self.repository.create_reference(
            bucket=bucket,
            object_name=object_name,
            image_type=image_type,
            plate=normalized_plate,
            hash_sha256=hash_sha256,
            university_id=university_id,
            content_type=content_type,
            session_id=session_id,
        )

    def link_evidence_to_session(self, image_id: str | None, session_id: str, plate: str) -> None:
        if not image_id:
            return
        self.repository.link_to_session(image_id=image_id, session_id=session_id, plate=plate)

    def get_image_bytes(self, image_id: str) -> tuple[bytes, str] | None:
        evidence = self.repository.get(image_id)
        if evidence is None:
            return None
        payload = self.storage.download_object(
            bucket=evidence["bucket"],
            object_name=evidence["object_name"],
        )
        return payload, "image/jpeg"

    def _resolve_bucket(self, image_type: str) -> str:
        if image_type.startswith("face_"):
            return settings.minio_bucket_faces
        if image_type.startswith("plate_"):
            return settings.minio_bucket_plates
        return settings.minio_bucket_evidence

    def _build_object_name(self, *, filename: str, image_type: str, plate: str) -> str:
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", filename or "evidence.bin").strip("-") or "evidence.bin"
        stamp = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        return f"{stamp}/{image_type}/{plate}-{uuid4().hex[:12]}-{safe_name}"
