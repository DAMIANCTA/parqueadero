import logging
from uuid import uuid4

from config import settings
from repositories.evidence_repository import EvidenceRepository
from repositories.face_repository import FaceRepository
from repositories.temporary_user_repository import TemporaryUserRepository


logger = logging.getLogger(__name__)


class TemporaryUserService:
    """Crea usuarios temporales de visitantes en la entrada.

    Al ingresar un visitante no registrado, enrola su rostro en
    ``face-service`` y persiste un "usuario temporal" (BD core) con
    caducidad, amarrado a la placa, a la sesion y a la evidencia de entrada,
    para consulta forense posterior (``GET /evidence/by-plate/{plate}``).

    Todas las llamadas a dependencias externas (face-service, BD core, BD de
    evidencia) pueden inyectarse para pruebas.
    """

    def __init__(
        self,
        face_repository: FaceRepository | None = None,
        temporary_user_repository: TemporaryUserRepository | None = None,
        evidence_repository: EvidenceRepository | None = None,
    ) -> None:
        self.face_service = face_repository or FaceRepository()
        self.repository = temporary_user_repository or TemporaryUserRepository()
        self.evidence_repository = evidence_repository or EvidenceRepository()

    def register_from_entry(
        self,
        *,
        university_id: str,
        plate_text: str,
        session_id: str | None,
        gate_id: str | None,
        face_evidence_id: str | None,
        face_fallback_id: str | None,
        plate_evidence_id: str | None = None,
        liveness_score: float | None = None,
    ) -> dict:
        """Enrola el rostro del visitante y crea su usuario temporal.

        Devuelve el registro del usuario temporal. Lanza excepcion si la
        persistencia o el enrolado real fallan (el llamador decide como
        manejarlo; en la entrada se trata como best-effort).
        """
        temp_user_id = str(uuid4())
        entry_reference = self._resolve_face_reference(
            evidence_id=face_evidence_id,
            fallback_id=face_fallback_id,
            plate_text=plate_text,
            image_type="face_entry",
        )
        enrollment = self.face_service.enroll(
            university_id=university_id,
            person_id=temp_user_id,
            image_reference=entry_reference,
        )
        record = self.repository.create(
            temp_user_id=temp_user_id,
            university_id=university_id,
            plate=plate_text,
            full_name=f"Visitante {plate_text}",
            face_template_id=enrollment.get("template_id"),
            entry_face_evidence_id=face_evidence_id,
            entry_plate_evidence_id=plate_evidence_id,
            entry_session_id=session_id,
            entry_gate_id=gate_id,
            face_model_name=enrollment.get("model_name"),
            liveness_score=liveness_score,
            metadata={
                "entry_face_reference": entry_reference,
                "enrollment_mode": enrollment.get("mode"),
            },
        )
        logger.info(
            "temporary_user created temp_user_id=%s plate=%s template_id=%s mode=%s",
            record["id"],
            plate_text,
            enrollment.get("template_id"),
            enrollment.get("mode"),
        )
        return record

    def _resolve_face_reference(
        self,
        *,
        evidence_id: str | None,
        fallback_id: str | None,
        plate_text: str,
        image_type: str,
    ) -> dict:
        """Construye una referencia de imagen para face-service.

        Intenta resolver la referencia real de MinIO desde ``image_evidence``;
        si no hay evidencia registrada (o falla la consulta) sintetiza una
        referencia estable a partir de la placa y el id de captura para que el
        flujo siga siendo funcional en desarrollo/pruebas.
        """
        if evidence_id:
            try:
                evidence = self.evidence_repository.get(evidence_id)
                if evidence:
                    return {
                        "bucket": evidence.get("bucket") or settings.minio_bucket_faces,
                        "object_path": evidence.get("object_name") or f"{plate_text}/{evidence_id}",
                        "sha256_hash": evidence.get("hash_sha256"),
                        "content_type": "image/jpeg",
                        "image_type": image_type,
                    }
            except Exception as exc:  # noqa: BLE001 - degradar a referencia sintetica
                logger.warning("evidence lookup failed evidence_id=%s error=%s", evidence_id, exc)

        token = fallback_id or evidence_id or "unknown"
        return {
            "bucket": settings.minio_bucket_faces,
            "object_path": f"{plate_text}/{token}.jpg",
            "sha256_hash": None,
            "content_type": "image/jpeg",
            "image_type": image_type,
        }
