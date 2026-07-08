import logging
from datetime import UTC, datetime

from fastapi import HTTPException

from config import settings
from repositories.biometric_repository import BiometricRepository
from schemas.faces import (
    FaceCompareRequest,
    FaceCompareResponse,
    FaceConfigResponse,
    FaceDetectRequest,
    FaceDetectResponse,
    FaceEnrollRequest,
    FaceEnrollResponse,
    FaceLivenessCheckRequest,
    FaceLivenessCheckResponse,
    FaceLivenessRequest,
    FaceLivenessResponse,
    FaceValidationSummary,
    FaceVerifyRequest,
    FaceVerifyResponse,
    FaceVerifySessionRequest,
    FaceVerifySessionResponse,
    MinioImageReference,
)
from services.embedding_math import EmbeddingMath
from services.face_models import ComparisonResult, ImageReference
from services.insightface_provider import InsightFaceProvider
from services.minio_image_service import MinioImageService
from services.mock_face_provider import MockFaceProvider
from services.mock_liveness_provider import MockLivenessProvider
from services.prepared_face_providers import (
    CompreFacePreparedProvider,
    DeepFacePreparedProvider,
    InsightFacePreparedProvider,
)
from services.prepared_liveness_provider import PreparedLivenessProvider
from services.providers.face_recognition_provider import FaceRecognitionProvider


logger = logging.getLogger(__name__)


class FaceRecognitionService:
    def __init__(self) -> None:
        self.repository = BiometricRepository()
        self.embedding_math = EmbeddingMath()
        self.minio_service = MinioImageService()
        self.insightface_provider = InsightFaceProvider()
        self.face_recognition_provider = FaceRecognitionProvider()

    def get_config(self) -> FaceConfigResponse:
        active_provider = self._resolve_face_provider()
        active_capabilities = self._capabilities_for_provider(active_provider)
        insightface_capabilities = self.insightface_provider.capabilities()
        face_recognition_capabilities = self.face_recognition_provider.capabilities()
        logger.info(
            "face-service config environment=%s mode=%s provider=%s active_provider=%s provider_available=%s model_loaded=%s model_error=%s",
            settings.environment,
            settings.face_service_mode,
            settings.face_real_provider,
            active_capabilities["active_provider"],
            active_capabilities["provider_available"],
            active_capabilities["model_loaded"],
            active_capabilities["model_error"],
        )
        return FaceConfigResponse(
            environment=settings.environment,
            face_service_mode=settings.face_service_mode,
            face_real_provider=settings.face_real_provider,
            similarity_threshold=settings.face_similarity_threshold,
            liveness_threshold=settings.face_liveness_threshold,
            embedding_dimensions=active_capabilities["embedding_dimensions"],
            opencv_available=active_capabilities["opencv_available"],
            insightface_available=insightface_capabilities["insightface_available"],
            face_recognition_available=face_recognition_capabilities["face_recognition_available"],
            provider_available=active_capabilities["provider_available"],
            model_loaded=active_capabilities["model_loaded"],
            model_error=active_capabilities["model_error"],
            active_provider=active_capabilities["active_provider"],
        )

    def detect(self, payload: FaceDetectRequest) -> FaceDetectResponse:
        provider = self._resolve_face_provider()
        logger.info(
            "face-service detect_request image_id=%s university_id=%s session_id=%s person_id=%s mode=%s provider=%s",
            payload.image_id,
            payload.university_id,
            payload.session_id,
            payload.person_id,
            settings.face_service_mode,
            provider.model_name,
        )
        evidence = self._get_existing_image(payload.image_id)
        image_reference = self._reference_from_evidence(evidence)
        try:
            image_bytes = self.minio_service.download_bytes(
                bucket=image_reference.bucket,
                object_path=image_reference.object_path,
            )
        except Exception as exc:
            logger.warning(
                "face-service detect download_failed image_id=%s object_path=%s error=%s",
                payload.image_id,
                image_reference.object_path,
                exc,
            )
            return FaceDetectResponse(
                detected=False,
                match=None,
                similarity=None,
                threshold=None,
                image_id=payload.image_id,
                session_id=payload.session_id,
                template_id=None,
                bounding_box=None,
                model_name=provider.model_name,
                provider=provider.model_name,
                mode=settings.face_service_mode,
                quality_score=None,
                embedding_size=0,
                warnings=["MINIO_DOWNLOAD_FAILED"],
                detected_at=datetime.now(UTC),
                stored_in_biometric_db=False,
            )
        analysis = provider.analyze_face(
            image_reference=image_reference,
            image_bytes=image_bytes,
            person_id=payload.session_id or payload.person_id,
            quality_score_hint=payload.quality_score_hint,
        )
        self._log_analysis(
            operation="detect",
            image_id=payload.image_id,
            analysis=analysis,
            extra={
                "session_id": payload.session_id,
                "person_id": payload.person_id,
                "provider_requested": provider.model_name,
            },
        )
        if not analysis.detected or analysis.embedding is None:
            return FaceDetectResponse(
                detected=False,
                match=None,
                similarity=None,
                threshold=None,
                image_id=payload.image_id,
                session_id=payload.session_id,
                template_id=None,
                bounding_box=self._bbox_schema(analysis.bounding_box),
                model_name=analysis.provider_name,
                provider=analysis.provider_name,
                mode=analysis.mode_used,
                quality_score=None,
                embedding_size=0,
                warnings=analysis.warnings,
                detected_at=datetime.now(UTC),
                stored_in_biometric_db=False,
            )

        person_reference = payload.session_id or payload.person_id
        template_id = None
        if person_reference:
            template = self.repository.create_face_template(
                university_id=payload.university_id,
                person_id=person_reference,
                image_evidence_id=payload.image_id,
                image_reference=image_reference,
                embedding=analysis.embedding,
                encrypted=bool(evidence.get("encrypted", True)),
                expires_at=evidence.get("expires_at"),
            )
            template_id = template.template_id
            logger.info(
                "face-service detect template_stored image_id=%s template_id=%s person_reference=%s embedding_size=%s",
                payload.image_id,
                template_id,
                person_reference,
                len(analysis.embedding.vector),
            )

        return FaceDetectResponse(
            detected=True,
            match=None,
            similarity=None,
            threshold=None,
            image_id=payload.image_id,
            session_id=payload.session_id,
            template_id=template_id,
            bounding_box=self._bbox_schema(analysis.bounding_box),
            model_name=analysis.embedding.model_name,
            provider=analysis.provider_name,
            mode=analysis.mode_used,
            quality_score=analysis.embedding.quality_score,
            embedding_size=len(analysis.embedding.vector),
            warnings=analysis.warnings,
            detected_at=datetime.now(UTC),
            stored_in_biometric_db=template_id is not None,
        )

    def verify_session(self, payload: FaceVerifySessionRequest) -> FaceVerifySessionResponse:
        provider = self._resolve_face_provider()
        template = self.repository.get_latest_template(payload.university_id, payload.session_id)
        if template is None:
            raise HTTPException(status_code=404, detail="No face template stored for this session")
        logger.info(
            "face-service verify_session_request probe_image_id=%s session_id=%s template_id=%s provider=%s threshold=%s",
            payload.probe_image_id,
            payload.session_id,
            template.template_id,
            provider.model_name,
            payload.similarity_threshold or settings.face_similarity_threshold,
        )

        evidence = self._get_existing_image(payload.probe_image_id)
        probe_reference = self._reference_from_evidence(evidence)
        try:
            probe_bytes = self.minio_service.download_bytes(
                bucket=probe_reference.bucket,
                object_path=probe_reference.object_path,
            )
        except Exception as exc:
            logger.warning(
                "face-service verify_session download_failed image_id=%s object_path=%s error=%s",
                payload.probe_image_id,
                probe_reference.object_path,
                exc,
            )
            log_id = self.repository.create_biometric_log(
                university_id=payload.university_id,
                person_id=payload.session_id,
                template_id=template.template_id,
                image_evidence_id=payload.probe_image_id,
                operation_type="exit_validation",
                model_name=provider.model_name,
                similarity_score=0.0,
                quality_score=None,
                liveness_score=None,
                decision="error",
                metadata={"warnings": ["MINIO_DOWNLOAD_FAILED"]},
                session_reference_id=payload.session_id,
                gate_reference_id=payload.gate_id,
            )
            return FaceVerifySessionResponse(
                detected=False,
                match=False,
                similarity=0.0,
                threshold=payload.similarity_threshold or settings.face_similarity_threshold,
                image_id=payload.probe_image_id,
                session_id=payload.session_id,
                template_id=template.template_id,
                bounding_box=None,
                model_name=provider.model_name,
                provider=provider.model_name,
                mode=settings.face_service_mode,
                quality_score=None,
                embedding_size=0,
                warnings=["MINIO_DOWNLOAD_FAILED"],
                biometric_log_id=log_id,
                probe_image_id=payload.probe_image_id,
            )
        analysis = provider.analyze_face(
            image_reference=probe_reference,
            image_bytes=probe_bytes,
            person_id=payload.session_id,
            quality_score_hint=None,
        )
        self._log_analysis(
            operation="verify_session_probe",
            image_id=payload.probe_image_id,
            analysis=analysis,
            extra={
                "session_id": payload.session_id,
                "template_id": template.template_id,
                "provider_requested": provider.model_name,
            },
        )
        if not analysis.detected or analysis.embedding is None:
            log_id = self.repository.create_biometric_log(
                university_id=payload.university_id,
                person_id=payload.session_id,
                template_id=template.template_id,
                image_evidence_id=payload.probe_image_id,
                operation_type="exit_validation",
                model_name=analysis.provider_name,
                similarity_score=0.0,
                quality_score=None,
                liveness_score=None,
                decision="error",
                metadata={"warnings": analysis.warnings},
                session_reference_id=payload.session_id,
                gate_reference_id=payload.gate_id,
            )
            return FaceVerifySessionResponse(
                detected=False,
                match=False,
                similarity=0.0,
                threshold=payload.similarity_threshold or settings.face_similarity_threshold,
                image_id=payload.probe_image_id,
                session_id=payload.session_id,
                template_id=template.template_id,
                bounding_box=self._bbox_schema(analysis.bounding_box),
                model_name=analysis.provider_name,
                provider=analysis.provider_name,
                mode=analysis.mode_used,
                quality_score=None,
                embedding_size=0,
                warnings=analysis.warnings,
                biometric_log_id=log_id,
                probe_image_id=payload.probe_image_id,
            )

        threshold = payload.similarity_threshold or settings.face_similarity_threshold
        comparison = self._compare_embeddings(
            left=template.embedding.vector,
            right=analysis.embedding.vector,
            threshold=threshold,
            model_name=analysis.embedding.model_name,
            provider=provider,
        )
        log_id = self.repository.create_biometric_log(
            university_id=payload.university_id,
            person_id=payload.session_id,
            template_id=template.template_id,
            image_evidence_id=payload.probe_image_id,
            operation_type="exit_validation",
            model_name=analysis.embedding.model_name,
            similarity_score=comparison.score,
            quality_score=analysis.embedding.quality_score,
            liveness_score=None,
            decision="approved" if comparison.match else "rejected",
            metadata={"warnings": analysis.warnings},
            session_reference_id=payload.session_id,
            gate_reference_id=payload.gate_id,
        )
        logger.info(
            "face-service verify_session_result image_id=%s session_id=%s metric=%s operator=%s score=%s threshold=%s match=%s bbox=%s warnings=%s",
            payload.probe_image_id,
            payload.session_id,
            comparison.metric,
            comparison.operator,
            comparison.score,
            comparison.threshold,
            comparison.match,
            self._bbox_to_dict(analysis.bounding_box),
            analysis.warnings,
        )
        return FaceVerifySessionResponse(
            detected=True,
            match=comparison.match,
            similarity=comparison.score,
            threshold=comparison.threshold,
            image_id=payload.probe_image_id,
            session_id=payload.session_id,
            template_id=template.template_id,
            bounding_box=self._bbox_schema(analysis.bounding_box),
            model_name=comparison.model_name,
            provider=analysis.provider_name,
            mode=analysis.mode_used,
            quality_score=analysis.embedding.quality_score,
            embedding_size=len(analysis.embedding.vector),
            warnings=analysis.warnings,
            biometric_log_id=log_id,
            probe_image_id=payload.probe_image_id,
        )

    def enroll(self, payload: FaceEnrollRequest) -> FaceEnrollResponse:
        image_reference = self._map_reference(payload.image_reference)
        image_evidence_id = self.repository.create_image_evidence(
            university_id=payload.university_id,
            person_id=payload.person_id,
            image_reference=image_reference,
            encrypted=payload.encrypted,
            expires_at=payload.expires_at,
        )
        provider = self._resolve_face_provider()
        analysis = self._analyze_reference_image(
            image_reference=image_reference,
            provider=provider,
            person_id=payload.person_id,
            quality_score_hint=payload.quality_score_hint,
        )
        if not analysis.detected or analysis.embedding is None:
            raise HTTPException(status_code=422, detail="Face enrollment failed because no valid face was detected")
        embedding = analysis.embedding
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
        provider = self._resolve_face_provider()
        analysis = self._analyze_reference_image(
            image_reference=image_reference,
            provider=provider,
            person_id=payload.person_id,
            quality_score_hint=None,
        )
        if not analysis.detected or analysis.embedding is None:
            raise HTTPException(status_code=422, detail="Face verification failed because no valid face was detected")
        probe_embedding = analysis.embedding
        threshold = payload.similarity_threshold or settings.face_similarity_threshold
        comparison = self._compare_embeddings(
            left=template.embedding.vector,
            right=probe_embedding.vector,
            threshold=threshold,
            model_name=provider.model_name,
            provider=provider,
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
        if payload.source_image_reference and payload.target_image_reference and not payload.source_image_id and not payload.target_image_id:
            return self._compare_legacy_references(payload)

        provider = self._resolve_face_provider()
        source_reference, source_image_id = self._resolve_compare_input(
            image_id=payload.source_image_id,
            reference=payload.source_image_reference,
        )
        target_reference, target_image_id = self._resolve_compare_input(
            image_id=payload.target_image_id,
            reference=payload.target_image_reference,
        )
        try:
            source_bytes = self.minio_service.download_bytes(
                bucket=source_reference.bucket,
                object_path=source_reference.object_path,
            )
            target_bytes = self.minio_service.download_bytes(
                bucket=target_reference.bucket,
                object_path=target_reference.object_path,
            )
        except Exception as exc:
            logger.warning("face-service compare download_failed error=%s", exc)
            return FaceCompareResponse(
                detected=False,
                match=False,
                similarity=0.0,
                threshold=payload.similarity_threshold or settings.face_similarity_threshold,
                image_id=source_image_id,
                session_id=payload.session_id,
                template_id=None,
                bounding_box=None,
                model_name=provider.model_name,
                provider=provider.model_name,
                mode=settings.face_service_mode,
                quality_score=None,
                embedding_size=0,
                warnings=["MINIO_DOWNLOAD_FAILED"],
                biometric_log_id=self.repository.create_biometric_log(
                    university_id=payload.university_id,
                    person_id=None,
                    template_id=None,
                    image_evidence_id=source_image_id,
                    operation_type="compare",
                    model_name=provider.model_name,
                    similarity_score=0.0,
                    quality_score=None,
                    liveness_score=None,
                    decision="error",
                    metadata={"warnings": ["MINIO_DOWNLOAD_FAILED"]},
                    session_reference_id=payload.session_id,
                    gate_reference_id=payload.gate_id,
                ),
                source_image_reference=payload.source_image_reference,
                target_image_reference=payload.target_image_reference,
                source_image_id=source_image_id,
                target_image_id=target_image_id,
            )
        source_analysis = provider.analyze_face(
            image_reference=source_reference,
            image_bytes=source_bytes,
            person_id=None,
            quality_score_hint=None,
        )
        target_analysis = provider.analyze_face(
            image_reference=target_reference,
            image_bytes=target_bytes,
            person_id=None,
            quality_score_hint=None,
        )
        self._log_analysis(
            operation="compare_source",
            image_id=source_image_id,
            analysis=source_analysis,
            extra={"target_image_id": target_image_id, "provider_requested": provider.model_name},
        )
        self._log_analysis(
            operation="compare_target",
            image_id=target_image_id,
            analysis=target_analysis,
            extra={"source_image_id": source_image_id, "provider_requested": provider.model_name},
        )
        warnings = source_analysis.warnings + target_analysis.warnings
        comparison = ComparisonResult(
            match=False,
            score=0.0,
            threshold=payload.similarity_threshold or settings.face_similarity_threshold,
            model_name=provider.model_name,
            metric="distance" if self._uses_distance_metric(provider) else "similarity",
            operator="lte" if self._uses_distance_metric(provider) else "gte",
        )
        if source_analysis.embedding and target_analysis.embedding:
            comparison = self._compare_embeddings(
                left=source_analysis.embedding.vector,
                right=target_analysis.embedding.vector,
                threshold=payload.similarity_threshold or settings.face_similarity_threshold,
                model_name=source_analysis.embedding.model_name,
                provider=provider,
            )
        log_id = self.repository.create_biometric_log(
            university_id=payload.university_id,
            person_id=None,
            template_id=None,
            image_evidence_id=source_image_id,
            operation_type="compare",
            model_name=comparison.model_name,
            similarity_score=comparison.score,
            quality_score=min(
                source_analysis.embedding.quality_score if source_analysis.embedding else 0.0,
                target_analysis.embedding.quality_score if target_analysis.embedding else 0.0,
            ),
            liveness_score=None,
            decision="approved" if comparison.match else "rejected",
            metadata={"warnings": warnings, "target_image_id": target_image_id},
            session_reference_id=payload.session_id,
            gate_reference_id=payload.gate_id,
        )
        logger.info(
            "face-service compare_result source_image_id=%s target_image_id=%s metric=%s operator=%s score=%s threshold=%s match=%s warnings=%s",
            source_image_id,
            target_image_id,
            comparison.metric,
            comparison.operator,
            comparison.score,
            comparison.threshold,
            comparison.match,
            warnings,
        )
        return FaceCompareResponse(
            detected=bool(source_analysis.detected and target_analysis.detected),
            match=comparison.match,
            similarity=comparison.score,
            threshold=comparison.threshold,
            image_id=source_image_id,
            session_id=payload.session_id,
            template_id=None,
            bounding_box=self._bbox_schema(source_analysis.bounding_box),
            model_name=comparison.model_name,
            provider=provider.model_name,
            mode=settings.face_service_mode,
            quality_score=source_analysis.embedding.quality_score if source_analysis.embedding else None,
            embedding_size=len(source_analysis.embedding.vector) if source_analysis.embedding else 0,
            warnings=warnings,
            biometric_log_id=log_id,
            source_image_reference=payload.source_image_reference,
            target_image_reference=payload.target_image_reference,
            source_image_id=source_image_id,
            target_image_id=target_image_id,
        )

    def _compare_legacy_references(self, payload: FaceCompareRequest) -> FaceCompareResponse:
        source_reference = self._map_reference(payload.source_image_reference)  # type: ignore[arg-type]
        target_reference = self._map_reference(payload.target_image_reference)  # type: ignore[arg-type]
        provider = self._resolve_face_provider()
        source_analysis = self._analyze_reference_image(
            image_reference=source_reference,
            provider=provider,
            person_id=None,
            quality_score_hint=None,
        )
        target_analysis = self._analyze_reference_image(
            image_reference=target_reference,
            provider=provider,
            person_id=None,
            quality_score_hint=None,
        )
        if not source_analysis.detected or source_analysis.embedding is None:
            raise HTTPException(status_code=422, detail="Source face image did not produce a valid embedding")
        if not target_analysis.detected or target_analysis.embedding is None:
            raise HTTPException(status_code=422, detail="Target face image did not produce a valid embedding")
        source_embedding = source_analysis.embedding
        target_embedding = target_analysis.embedding
        comparison = self._compare_embeddings(
            left=source_embedding.vector,
            right=target_embedding.vector,
            threshold=payload.similarity_threshold or settings.face_similarity_threshold,
            model_name=source_embedding.model_name,
            provider=provider,
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
            model_name=comparison.model_name,
            similarity_score=comparison.score,
            quality_score=min(source_embedding.quality_score, target_embedding.quality_score),
            liveness_score=None,
            decision="approved" if comparison.match else "rejected",
            metadata={"mode": settings.face_service_mode},
            session_reference_id=payload.session_id,
            gate_reference_id=payload.gate_id,
        )
        return FaceCompareResponse(
            detected=True,
            match=comparison.match,
            similarity=comparison.score,
            threshold=comparison.threshold,
            image_id=image_evidence_id,
            session_id=payload.session_id,
            template_id=None,
            bounding_box=None,
            model_name=comparison.model_name,
            provider=provider.model_name,
            mode=settings.face_service_mode,
            quality_score=min(source_embedding.quality_score, target_embedding.quality_score),
            embedding_size=len(source_embedding.vector),
            warnings=source_analysis.warnings + target_analysis.warnings,
            biometric_log_id=log_id,
            source_image_reference=payload.source_image_reference,
            target_image_reference=payload.target_image_reference,
            source_image_id=None,
            target_image_id=None,
        )

    def liveness(self, payload: FaceLivenessRequest) -> FaceLivenessResponse:
        evidence = self._get_existing_image(payload.image_id)
        image_reference = self._reference_from_evidence(evidence)
        threshold = payload.liveness_threshold or settings.face_liveness_threshold
        provider = self._resolve_liveness_provider()
        result = provider.check(
            image_reference=image_reference,
            threshold=threshold,
            challenge_type=payload.challenge_type,
        )
        log_id = self.repository.create_biometric_log(
            university_id=payload.university_id,
            person_id=payload.person_id or payload.session_id,
            template_id=None,
            image_evidence_id=payload.image_id,
            operation_type="liveness",
            model_name=result.model_name,
            similarity_score=None,
            quality_score=None,
            liveness_score=result.score,
            decision="passed" if result.passed else "failed",
            metadata={"challenge_type": payload.challenge_type},
            session_reference_id=payload.session_id,
        )
        warnings = [] if result.passed else ["LIVENESS_FAILED"]
        logger.info(
            "face-service liveness_result image_id=%s session_id=%s person_id=%s score=%s threshold=%s passed=%s provider=%s warnings=%s",
            payload.image_id,
            payload.session_id,
            payload.person_id,
            result.score,
            result.threshold,
            result.passed,
            result.model_name,
            warnings,
        )
        return FaceLivenessResponse(
            passed=result.passed,
            score=result.score,
            threshold=result.threshold,
            biometric_log_id=log_id,
            model_name=result.model_name,
            mode=settings.face_service_mode,
            image_id=payload.image_id,
            warnings=warnings,
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
        provider=None,
    ) -> ComparisonResult:
        if provider is not None and hasattr(provider, "compare_embeddings"):
            return provider.compare_embeddings(
                source_embedding=left,
                target_embedding=right,
                threshold=threshold,
            )
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
        if provider == "face_recognition":
            return self.face_recognition_provider
        if provider == "deepface":
            return DeepFacePreparedProvider()
        if provider == "compreface":
            return CompreFacePreparedProvider()
        if provider == "insightface" and settings.face_service_mode.lower() == "real":
            return InsightFacePreparedProvider()
        return InsightFacePreparedProvider()

    def _resolve_face_provider(self):
        if settings.face_service_mode.lower() == "mock":
            return MockFaceProvider()
        if settings.face_real_provider.lower() == "face_recognition":
            return self.face_recognition_provider
        if settings.face_real_provider.lower() == "insightface":
            return self.insightface_provider
        if settings.face_real_provider.lower() == "deepface":
            return DeepFacePreparedProvider()
        if settings.face_real_provider.lower() == "compreface":
            return CompreFacePreparedProvider()
        return InsightFacePreparedProvider()

    def _resolve_liveness_provider(self):
        if settings.face_service_mode.lower() == "mock":
            return MockLivenessProvider()
        return PreparedLivenessProvider()

    def _capabilities_for_provider(self, provider) -> dict:
        if hasattr(provider, "capabilities"):
            return provider.capabilities()
        return {
            "opencv_available": False,
            "insightface_available": False,
            "face_recognition_available": False,
            "provider_available": True,
            "model_loaded": True,
            "model_error": None,
            "active_provider": getattr(provider, "model_name", settings.face_real_provider),
            "embedding_dimensions": settings.face_embedding_dimensions,
        }

    def _uses_distance_metric(self, provider) -> bool:
        provider_name = getattr(provider, "provider_name", "") or getattr(provider, "model_name", "")
        return "face_recognition" in str(provider_name).lower()

    def _analyze_reference_image(
        self,
        *,
        image_reference: ImageReference,
        provider,
        person_id: str | None,
        quality_score_hint: float | None,
    ):
        image_bytes = b""
        try:
            image_bytes = self.minio_service.download_bytes(
                bucket=image_reference.bucket,
                object_path=image_reference.object_path,
            )
        except Exception as exc:
            if self._requires_real_image_bytes(provider):
                logger.warning(
                    "face-service reference_analysis download_failed object_path=%s provider=%s error=%s",
                    image_reference.object_path,
                    getattr(provider, "model_name", "unknown"),
                    exc,
                )
                raise HTTPException(status_code=503, detail=f"Unable to download face image from MinIO: {exc}") from exc
        analysis = provider.analyze_face(
            image_reference=image_reference,
            image_bytes=image_bytes,
            person_id=person_id,
            quality_score_hint=quality_score_hint,
        )
        self._log_analysis(
            operation="reference_analysis",
            image_id=None,
            analysis=analysis,
            extra={
                "object_path": image_reference.object_path,
                "provider_requested": getattr(provider, "model_name", "unknown"),
            },
        )
        return analysis

    def _requires_real_image_bytes(self, provider) -> bool:
        provider_name = getattr(provider, "provider_name", "") or getattr(provider, "model_name", "")
        normalized = str(provider_name).lower()
        return normalized in {"insightface", "face_recognition"} or normalized.startswith("insightface:")

    def _map_reference(self, reference: MinioImageReference) -> ImageReference:
        return ImageReference(
            bucket=reference.bucket or settings.face_default_bucket,
            object_path=reference.object_path,
            object_version=reference.object_version,
            sha256_hash=reference.sha256_hash,
            content_type=reference.content_type,
            image_type=reference.image_type,
        )

    def _get_existing_image(self, image_id: str) -> dict:
        evidence = self.repository.get_image_evidence(image_id)
        if evidence is None:
            raise HTTPException(status_code=404, detail="Face evidence image was not found")
        return evidence

    def _reference_from_evidence(self, evidence: dict) -> ImageReference:
        return ImageReference(
            bucket=evidence.get("minio_bucket") or evidence.get("bucket") or settings.face_default_bucket,
            object_path=evidence.get("object_path") or evidence.get("object_name") or "",
            object_version=evidence.get("object_version"),
            sha256_hash=evidence.get("sha256_hash") or evidence.get("hash_sha256"),
            content_type=evidence.get("content_type") or "image/jpeg",
            image_type=evidence.get("image_type") or "face_capture",
        )

    def _resolve_compare_input(
        self,
        *,
        image_id: str | None,
        reference: MinioImageReference | None,
    ) -> tuple[ImageReference, str]:
        if image_id:
            evidence = self._get_existing_image(image_id)
            return self._reference_from_evidence(evidence), image_id
        if reference:
            stored_image_id = self.repository.create_image_evidence(
                university_id="shared",
                person_id=None,
                image_reference=self._map_reference(reference),
                encrypted=True,
                expires_at=None,
            )
            return self._map_reference(reference), stored_image_id
        raise HTTPException(status_code=422, detail="Either image_id or image_reference must be provided")

    def _bbox_to_dict(self, bbox) -> dict | None:
        if bbox is None:
            return None
        return {
            "x": bbox.x,
            "y": bbox.y,
            "width": bbox.width,
            "height": bbox.height,
        }

    def _bbox_schema(self, bbox):
        from schemas.faces import FaceBoundingBoxResponse

        if bbox is None:
            return None
        return FaceBoundingBoxResponse(
            x=bbox.x,
            y=bbox.y,
            width=bbox.width,
            height=bbox.height,
        )

    def _log_analysis(
        self,
        *,
        operation: str,
        image_id: str | None,
        analysis,
        extra: dict | None = None,
    ) -> None:
        details = extra or {}
        logger.info(
            "face-service %s image_id=%s detected=%s bbox=%s embedding_generated=%s embedding_size=%s quality_score=%s provider=%s mode=%s warnings=%s extra=%s",
            operation,
            image_id,
            analysis.detected,
            self._bbox_to_dict(analysis.bounding_box),
            analysis.embedding is not None,
            len(analysis.embedding.vector) if analysis.embedding else 0,
            analysis.embedding.quality_score if analysis.embedding else None,
            analysis.provider_name,
            analysis.mode_used,
            analysis.warnings,
            details,
        )
