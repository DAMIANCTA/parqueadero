from fastapi import HTTPException

from config import settings
from repositories.biometric_repository import BiometricRepository
from schemas.faces import (
    FaceCompareRequest,
    FaceCompareResponse,
    FaceEnrollRequest,
    FaceEnrollResponse,
    FaceLivenessCheckRequest,
    FaceLivenessCheckResponse,
    FaceVerifyRequest,
    FaceVerifyResponse,
    MinioImageReference,
)
from services.embedding_math import EmbeddingMath
from services.face_models import ComparisonResult, ImageReference
from services.mock_face_provider import MockFaceProvider
from services.mock_liveness_provider import MockLivenessProvider
from services.prepared_face_providers import (
    CompreFacePreparedProvider,
    DeepFacePreparedProvider,
    InsightFacePreparedProvider,
)
from services.prepared_liveness_provider import PreparedLivenessProvider


class FaceRecognitionService:
    def __init__(self) -> None:
        self.repository = BiometricRepository()
        self.embedding_math = EmbeddingMath()

    def enroll(self, payload: FaceEnrollRequest) -> FaceEnrollResponse:
        image_reference = self._map_reference(payload.image_reference)
        image_evidence_id = self.repository.create_image_evidence(
            university_id=payload.university_id,
            person_id=payload.person_id,
            image_reference=image_reference,
            encrypted=payload.encrypted,
            expires_at=payload.expires_at,
        )
        provider = self._resolve_embedding_provider()
        embedding = provider.generate_embedding(
            image_reference=image_reference,
            person_id=payload.person_id,
            quality_score_hint=payload.quality_score_hint,
        )
        template = self.repository.create_face_template(
            university_id=payload.university_id,
            person_id=payload.person_id,
            image_evidence_id=image_evidence_id,
            image_reference=image_reference,
            embedding=embedding,
            encrypted=payload.encrypted,
            expires_at=payload.expires_at,
        )
        return FaceEnrollResponse(
            enrolled=True,
            template_id=template.template_id,
            image_evidence_id=image_evidence_id,
            university_id=payload.university_id,
            person_id=payload.person_id,
            model_name=embedding.model_name,
            embedding_size=len(embedding.vector),
            quality_score=embedding.quality_score,
            mode=settings.face_service_mode,
            image_reference=payload.image_reference,
            stored_in_biometric_db=True,
        )

    def verify(self, payload: FaceVerifyRequest) -> FaceVerifyResponse:
        template = (
            self.repository.get_template(payload.template_id)
            if payload.template_id
            else self.repository.get_latest_template(payload.university_id, payload.person_id)
        )
        if template is None:
            raise HTTPException(status_code=404, detail="Face template not found for verification")

        image_reference = self._map_reference(payload.probe_image_reference)
        image_evidence_id = self.repository.create_image_evidence(
            university_id=payload.university_id,
            person_id=payload.person_id,
            image_reference=image_reference,
            encrypted=True,
            expires_at=None,
        )
        provider = self._resolve_embedding_provider()
        probe_embedding = provider.generate_embedding(
            image_reference=image_reference,
            person_id=payload.person_id,
            quality_score_hint=None,
        )
        threshold = payload.similarity_threshold or settings.face_similarity_threshold
        comparison = self._compare_embeddings(
            left=template.embedding.vector,
            right=probe_embedding.vector,
            threshold=threshold,
            model_name=provider.model_name,
        )
        log_id = self.repository.create_biometric_log(
            university_id=payload.university_id,
            person_id=payload.person_id,
            template_id=template.template_id,
            image_evidence_id=image_evidence_id,
            operation_type="verify",
            model_name=provider.model_name,
            similarity_score=comparison.score,
            quality_score=probe_embedding.quality_score,
            liveness_score=None,
            decision="match" if comparison.match else "no_match",
            metadata={"mode": settings.face_service_mode},
        )
        return FaceVerifyResponse(
            match=comparison.match,
            score=comparison.score,
            threshold=comparison.threshold,
            template_id=template.template_id,
            biometric_log_id=log_id,
            model_name=comparison.model_name,
            mode=settings.face_service_mode,
            image_reference=payload.probe_image_reference,
        )

    def compare(self, payload: FaceCompareRequest) -> FaceCompareResponse:
        source_reference = self._map_reference(payload.source_image_reference)
        target_reference = self._map_reference(payload.target_image_reference)
        provider = self._resolve_embedding_provider()
        source_embedding = provider.generate_embedding(image_reference=source_reference, person_id=None, quality_score_hint=None)
        target_embedding = provider.generate_embedding(image_reference=target_reference, person_id=None, quality_score_hint=None)
        threshold = payload.similarity_threshold or settings.face_similarity_threshold
        comparison = self._compare_embeddings(
            left=source_embedding.vector,
            right=target_embedding.vector,
            threshold=threshold,
            model_name=provider.model_name,
        )
        image_evidence_id = self.repository.create_image_evidence(
            university_id=payload.university_id or "shared",
            person_id=None,
            image_reference=source_reference,
            encrypted=True,
            expires_at=None,
        )
        log_id = self.repository.create_biometric_log(
            university_id=payload.university_id,
            person_id=None,
            template_id=None,
            image_evidence_id=image_evidence_id,
            operation_type="compare",
            model_name=provider.model_name,
            similarity_score=comparison.score,
            quality_score=min(source_embedding.quality_score, target_embedding.quality_score),
            liveness_score=None,
            decision="match" if comparison.match else "no_match",
            metadata={
                "mode": settings.face_service_mode,
                "target_reference": payload.target_image_reference.object_path,
            },
        )
        return FaceCompareResponse(
            match=comparison.match,
            score=comparison.score,
            threshold=comparison.threshold,
            biometric_log_id=log_id,
            model_name=comparison.model_name,
            mode=settings.face_service_mode,
            source_image_reference=payload.source_image_reference,
            target_image_reference=payload.target_image_reference,
        )

    def liveness_check(self, payload: FaceLivenessCheckRequest) -> FaceLivenessCheckResponse:
        image_reference = self._map_reference(payload.image_reference)
        image_evidence_id = self.repository.create_image_evidence(
            university_id=payload.university_id or "shared",
            person_id=payload.person_id,
            image_reference=image_reference,
            encrypted=True,
            expires_at=None,
        )
        threshold = payload.liveness_threshold or settings.face_liveness_threshold
        provider = self._resolve_liveness_provider()
        result = provider.check(
            image_reference=image_reference,
            threshold=threshold,
            challenge_type=payload.challenge_type,
        )
        log_id = self.repository.create_biometric_log(
            university_id=payload.university_id,
            person_id=payload.person_id,
            template_id=None,
            image_evidence_id=image_evidence_id,
            operation_type="liveness_check",
            model_name=provider.model_name,
            similarity_score=None,
            quality_score=None,
            liveness_score=result.score,
            decision="passed" if result.passed else "failed",
            metadata={"mode": settings.face_service_mode, "challenge_type": payload.challenge_type},
        )
        return FaceLivenessCheckResponse(
            passed=result.passed,
            score=result.score,
            threshold=result.threshold,
            biometric_log_id=log_id,
            model_name=result.model_name,
            mode=settings.face_service_mode,
            image_reference=payload.image_reference,
        )

    def _compare_embeddings(
        self,
        *,
        left: list[float],
        right: list[float],
        threshold: float,
        model_name: str,
    ) -> ComparisonResult:
        score = round(self.embedding_math.cosine_similarity(left, right), 4)
        return ComparisonResult(
            match=score >= threshold,
            score=score,
            threshold=threshold,
            model_name=model_name,
        )

    def _resolve_embedding_provider(self):
        if settings.face_service_mode.lower() == "mock":
            return MockFaceProvider()

        provider = settings.face_real_provider.lower()
        if provider == "deepface":
            return DeepFacePreparedProvider()
        if provider == "compreface":
            return CompreFacePreparedProvider()
        return InsightFacePreparedProvider()

    def _resolve_liveness_provider(self):
        if settings.face_service_mode.lower() == "mock":
            return MockLivenessProvider()
        return PreparedLivenessProvider()

    def _map_reference(self, reference: MinioImageReference) -> ImageReference:
        return ImageReference(
            bucket=reference.bucket or settings.face_default_bucket,
            object_path=reference.object_path,
            object_version=reference.object_version,
            sha256_hash=reference.sha256_hash,
            content_type=reference.content_type,
            image_type=reference.image_type,
        )
