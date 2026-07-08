import io
import logging
from typing import Any

from PIL import Image

from config import settings
from services.deterministic_face_provider import DeterministicFaceProvider
from services.face_models import FaceAnalysisResult, FaceBoundingBox, ImageReference


logger = logging.getLogger(__name__)

try:  # pragma: no cover - runtime dependency
    import cv2  # type: ignore
except Exception as exc:  # pragma: no cover - runtime dependency
    cv2 = None
    _cv2_error = str(exc)
else:
    _cv2_error = None

try:  # pragma: no cover - runtime dependency
    import numpy as np  # type: ignore
except Exception as exc:  # pragma: no cover - runtime dependency
    np = None
    _numpy_error = str(exc)
else:
    _numpy_error = None

try:  # pragma: no cover - runtime dependency
    from insightface.app import FaceAnalysis  # type: ignore
except Exception as exc:  # pragma: no cover - runtime dependency
    FaceAnalysis = None
    _insightface_error = str(exc)
else:
    _insightface_error = None


class InsightFaceProvider:
    _app: Any = None
    _model_error: str | None = None

    def __init__(self, *, fallback_model_name: str = "insightface-fallback") -> None:
        self._fallback = DeterministicFaceProvider(model_name=fallback_model_name)

    @property
    def model_name(self) -> str:
        app = self._ensure_app()
        if app is not None:
            return f"insightface:{settings.face_insightface_app_name}"
        return self._fallback.model_name

    @property
    def provider_name(self) -> str:
        return "insightface"

    @property
    def vector_dimensions(self) -> int:
        return 512

    def capabilities(self) -> dict[str, Any]:
        app = self._ensure_app()
        return {
            "opencv_available": cv2 is not None and np is not None,
            "insightface_available": FaceAnalysis is not None,
            "face_recognition_available": False,
            "provider_available": app is not None,
            "model_loaded": app is not None,
            "model_error": self._model_error,
            "active_provider": self.provider_name if app is not None else self.model_name,
            "embedding_dimensions": self.vector_dimensions,
        }

    def analyze_face(
        self,
        *,
        image_reference: ImageReference,
        image_bytes: bytes,
        person_id: str | None = None,
        quality_score_hint: float | None = None,
        allow_fallback: bool = True,
    ) -> FaceAnalysisResult:
        warnings: list[str] = []
        image = self._decode_image(image_bytes)
        if image is None:
            logger.warning(
                "face-service insightface_invalid_image object_path=%s bytes=%s",
                image_reference.object_path,
                len(image_bytes),
            )
            return FaceAnalysisResult(
                detected=False,
                embedding=None,
                bounding_box=None,
                provider_name=self.model_name,
                mode_used=settings.face_service_mode.lower(),
                warnings=["INVALID_IMAGE"],
            )

        app = self._ensure_app()
        if app is None:
            warnings.append("INSIGHTFACE_MODEL_UNAVAILABLE")
            logger.warning(
                "face-service insightface_unavailable object_path=%s allow_fallback=%s mode=%s warnings=%s",
                image_reference.object_path,
                allow_fallback,
                settings.face_service_mode.lower(),
                warnings,
            )
            if allow_fallback and settings.face_service_mode.lower() == "hybrid":
                result = self._fallback.analyze_face(
                    image_reference=image_reference,
                    image_bytes=image_bytes,
                    person_id=person_id,
                    quality_score_hint=quality_score_hint,
                )
                return FaceAnalysisResult(
                    detected=result.detected,
                    embedding=result.embedding,
                    bounding_box=FaceBoundingBox(x=0, y=0, width=image.shape[1], height=image.shape[0]),
                    provider_name=result.provider_name,
                    mode_used="hybrid-fallback",
                    warnings=warnings + result.warnings,
                )
            return FaceAnalysisResult(
                detected=False,
                embedding=None,
                bounding_box=None,
                provider_name=self.model_name,
                mode_used=settings.face_service_mode.lower(),
                warnings=warnings,
            )

        try:  # pragma: no cover - depends on runtime model
            faces = app.get(image)
        except Exception as exc:
            logger.exception("face-service insightface_detect_failed object_path=%s error=%s", image_reference.object_path, exc)
            warnings.append("FACE_DETECTION_RUNTIME_FAILED")
            if allow_fallback and settings.face_service_mode.lower() == "hybrid":
                result = self._fallback.analyze_face(
                    image_reference=image_reference,
                    image_bytes=image_bytes,
                    person_id=person_id,
                    quality_score_hint=quality_score_hint,
                )
                return FaceAnalysisResult(
                    detected=result.detected,
                    embedding=result.embedding,
                    bounding_box=FaceBoundingBox(x=0, y=0, width=image.shape[1], height=image.shape[0]),
                    provider_name=result.provider_name,
                    mode_used="hybrid-fallback",
                    warnings=warnings + result.warnings,
                )
            return FaceAnalysisResult(
                detected=False,
                embedding=None,
                bounding_box=None,
                provider_name=self.model_name,
                mode_used=settings.face_service_mode.lower(),
                warnings=warnings,
            )

        if not faces:
            logger.info(
                "face-service insightface_no_face object_path=%s shape=%sx%s",
                image_reference.object_path,
                image.shape[1],
                image.shape[0],
            )
            return FaceAnalysisResult(
                detected=False,
                embedding=None,
                bounding_box=None,
                provider_name=self.model_name,
                mode_used=settings.face_service_mode.lower(),
                warnings=["FACE_NOT_DETECTED"],
            )

        selected_face = max(
            faces,
            key=lambda face: float(
                (face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1])  # type: ignore[index]
            ),
        )
        bbox_values = [int(round(float(value))) for value in selected_face.bbox.tolist()]
        detection_score = float(getattr(selected_face, "det_score", 0.9))
        quality_score = quality_score_hint if quality_score_hint is not None else round(min(0.99, max(0.0, detection_score)), 4)
        embedding_vector = getattr(selected_face, "normed_embedding", None)
        if embedding_vector is None:
            embedding_vector = getattr(selected_face, "embedding", None)
        if embedding_vector is None:
            return FaceAnalysisResult(
                detected=False,
                embedding=None,
                bounding_box=FaceBoundingBox(
                    x=bbox_values[0],
                    y=bbox_values[1],
                    width=max(0, bbox_values[2] - bbox_values[0]),
                    height=max(0, bbox_values[3] - bbox_values[1]),
                ),
                provider_name=self.model_name,
                mode_used=settings.face_service_mode.lower(),
                warnings=["EMBEDDING_NOT_AVAILABLE"],
            )

        embedding = self._fallback.generate_embedding(
            image_reference=image_reference,
            person_id=person_id,
            quality_score_hint=quality_score,
        )
        embedding.vector = [round(float(value), 6) for value in embedding_vector.tolist()]
        embedding.model_name = self.model_name
        logger.info(
            "face-service insightface_face_selected object_path=%s detections=%s detection_score=%s bbox=%s quality_score=%s embedding_size=%s",
            image_reference.object_path,
            len(faces),
            round(detection_score, 4),
            bbox_values,
            quality_score,
            len(embedding.vector),
        )
        return FaceAnalysisResult(
            detected=True,
            embedding=embedding,
            bounding_box=FaceBoundingBox(
                x=bbox_values[0],
                y=bbox_values[1],
                width=max(0, bbox_values[2] - bbox_values[0]),
                height=max(0, bbox_values[3] - bbox_values[1]),
            ),
            provider_name=self.model_name,
            mode_used=settings.face_service_mode.lower(),
            warnings=[] if detection_score >= settings.face_detector_confidence_threshold else ["LOW_FACE_DETECTION_CONFIDENCE"],
        )

    def _ensure_app(self) -> Any:
        if self._app is not None:
            return self._app
        if FaceAnalysis is None or cv2 is None or np is None:
            errors = [part for part in (_cv2_error, _numpy_error, _insightface_error) if part]
            self._model_error = "; ".join(errors) if errors else "Missing runtime dependency"
            return None
        try:  # pragma: no cover - depends on runtime model
            app = FaceAnalysis(name=settings.face_insightface_app_name, root=settings.face_insightface_root)
            app.prepare(ctx_id=-1, det_size=(640, 640))
            self._app = app
            self._model_error = None
            logger.info(
                "face-service insightface_model_loaded app=%s root=%s",
                settings.face_insightface_app_name,
                settings.face_insightface_root,
            )
            return self._app
        except Exception as exc:
            self._model_error = str(exc)
            logger.warning(
                "face-service insightface_model_unavailable app=%s root=%s error=%s",
                settings.face_insightface_app_name,
                settings.face_insightface_root,
                exc,
            )
            return None

    def _decode_image(self, image_bytes: bytes):
        if cv2 is None or np is None:
            return None
        try:
            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            rgb_array = np.array(pil_image)
            return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        except Exception:
            return None
