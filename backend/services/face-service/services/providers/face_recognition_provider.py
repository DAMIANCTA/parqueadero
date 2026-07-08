import io
import logging
from typing import Any

from PIL import Image

from config import settings
from services.deterministic_face_provider import DeterministicFaceProvider
from services.face_models import ComparisonResult, FaceAnalysisResult, FaceBoundingBox, FaceEmbedding, ImageReference


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
    import face_recognition  # type: ignore
except Exception as exc:  # pragma: no cover - runtime dependency
    face_recognition = None
    _face_recognition_error = str(exc)
else:
    _face_recognition_error = None

try:  # pragma: no cover - runtime dependency
    import dlib  # type: ignore
except Exception as exc:  # pragma: no cover - runtime dependency
    dlib = None
    _dlib_error = str(exc)
else:
    _dlib_error = None


class FaceRecognitionProvider:
    def __init__(self, *, fallback_model_name: str = "face-recognition-fallback") -> None:
        self._fallback = DeterministicFaceProvider(model_name=fallback_model_name)
        self._loaded = False
        self._load_error: str | None = None

    @property
    def provider_name(self) -> str:
        return "face_recognition"

    @property
    def model_name(self) -> str:
        if self.is_available():
            return "face_recognition:dlib"
        return self._fallback.model_name

    @property
    def vector_dimensions(self) -> int:
        return 128

    def load(self) -> bool:
        if self._loaded:
            return True
        errors = [part for part in (_numpy_error, _face_recognition_error, _dlib_error) if part]
        if errors:
            self._load_error = "; ".join(errors)
            logger.warning("face-service face_recognition_provider_unavailable error=%s", self._load_error)
            return False
        self._loaded = True
        self._load_error = None
        logger.info("face-service face_recognition_provider_loaded provider=%s", self.model_name)
        return True

    def is_available(self) -> bool:
        return self.load()

    def capabilities(self) -> dict[str, Any]:
        available = self.is_available()
        return {
            "opencv_available": cv2 is not None and np is not None,
            "insightface_available": False,
            "face_recognition_available": face_recognition is not None and dlib is not None,
            "provider_available": available,
            "model_loaded": available,
            "model_error": self._load_error,
            "active_provider": self.provider_name if available else self.model_name,
            "embedding_dimensions": self.vector_dimensions,
        }

    def detect_face(self, image_source: bytes | Any) -> dict[str, Any]:
        image = self._prepare_image(image_source)
        if image is None or face_recognition is None or np is None:
            return {
                "detected": False,
                "bounding_box": None,
                "location": None,
                "warnings": ["INVALID_IMAGE" if image is None else "FACE_RECOGNITION_PROVIDER_UNAVAILABLE"],
            }

        try:
            locations = face_recognition.face_locations(image)
        except Exception as exc:  # pragma: no cover - runtime dependency
            logger.warning("face-service face_recognition_detect_failed error=%s", exc)
            return {
                "detected": False,
                "bounding_box": None,
                "location": None,
                "warnings": ["FACE_DETECTION_RUNTIME_FAILED"],
            }

        if not locations:
            return {
                "detected": False,
                "bounding_box": None,
                "location": None,
                "warnings": ["FACE_NOT_DETECTED"],
            }

        selected_location = max(
            locations,
            key=lambda location: max(0, location[1] - location[3]) * max(0, location[2] - location[0]),
        )
        top, right, bottom, left = [int(value) for value in selected_location]
        bounding_box = FaceBoundingBox(
            x=left,
            y=top,
            width=max(0, right - left),
            height=max(0, bottom - top),
        )
        return {
            "detected": True,
            "bounding_box": bounding_box,
            "location": selected_location,
            "warnings": [],
        }

    def generate_embedding(
        self,
        image_source: bytes | Any = None,
        *,
        image_reference: ImageReference | None = None,
        person_id: str | None = None,
        quality_score_hint: float | None = None,
        face_location: tuple[int, int, int, int] | None = None,
    ) -> FaceEmbedding | None:
        if image_source is None:
            if image_reference is None:
                return None
            return self._fallback.generate_embedding(
                image_reference=image_reference,
                person_id=person_id,
                quality_score_hint=quality_score_hint,
            )
        image = self._prepare_image(image_source)
        if image is None or face_recognition is None:
            return None

        locations = [face_location] if face_location else None
        try:
            encodings = face_recognition.face_encodings(image, known_face_locations=locations)
        except Exception as exc:  # pragma: no cover - runtime dependency
            logger.warning("face-service face_recognition_encoding_failed error=%s", exc)
            return None

        if not encodings:
            return None

        vector = [round(float(value), 6) for value in encodings[0].tolist()]
        quality_score = quality_score_hint
        if quality_score is None:
            quality_score = self._estimate_quality(image=image, face_location=face_location)
        return FaceEmbedding(
            vector=vector,
            model_name=self.model_name,
            quality_score=max(0.0, min(1.0, round(float(quality_score), 4))),
        )

    def compare_embeddings(
        self,
        *,
        source_embedding: list[float],
        target_embedding: list[float],
        threshold: float,
    ) -> ComparisonResult:
        if np is None:
            score = 1.0
            return ComparisonResult(
                match=False,
                score=score,
                threshold=threshold,
                model_name=self.model_name,
                metric="distance",
                operator="lte",
            )

        left = self._normalize_embedding(source_embedding)
        right = self._normalize_embedding(target_embedding)

        if face_recognition is not None:
            distance = float(face_recognition.face_distance([left], right)[0])
            match = bool(face_recognition.compare_faces([left], right, tolerance=threshold)[0])
        else:
            distance = float(np.linalg.norm(left - right))
            match = distance <= threshold

        return ComparisonResult(
            match=match,
            score=round(distance, 4),
            threshold=threshold,
            model_name=self.model_name,
            metric="distance",
            operator="lte",
        )

    def analyze_face(
        self,
        *,
        image_reference: ImageReference,
        image_bytes: bytes,
        person_id: str | None = None,
        quality_score_hint: float | None = None,
        allow_fallback: bool = True,
    ) -> FaceAnalysisResult:
        if not self.is_available():
            warnings = ["FACE_RECOGNITION_PROVIDER_UNAVAILABLE"]
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
                    bounding_box=result.bounding_box,
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

        detection = self.detect_face(image_bytes)
        if not detection["detected"]:
            return FaceAnalysisResult(
                detected=False,
                embedding=None,
                bounding_box=detection["bounding_box"],
                provider_name=self.model_name,
                mode_used=settings.face_service_mode.lower(),
                warnings=detection["warnings"],
            )

        embedding = self.generate_embedding(
            image_bytes,
            image_reference=image_reference,
            person_id=person_id,
            quality_score_hint=quality_score_hint,
            face_location=detection["location"],
        )
        if embedding is None:
            return FaceAnalysisResult(
                detected=False,
                embedding=None,
                bounding_box=detection["bounding_box"],
                provider_name=self.model_name,
                mode_used=settings.face_service_mode.lower(),
                warnings=["EMBEDDING_NOT_AVAILABLE"],
            )

        logger.info(
            "face-service face_recognition_face_selected object_path=%s bbox=%s embedding_size=%s quality_score=%s",
            image_reference.object_path,
            {
                "x": detection["bounding_box"].x,
                "y": detection["bounding_box"].y,
                "width": detection["bounding_box"].width,
                "height": detection["bounding_box"].height,
            },
            len(embedding.vector),
            embedding.quality_score,
        )
        return FaceAnalysisResult(
            detected=True,
            embedding=embedding,
            bounding_box=detection["bounding_box"],
            provider_name=self.model_name,
            mode_used=settings.face_service_mode.lower(),
            warnings=[],
        )

    def _prepare_image(self, image_source: bytes | Any):
        if np is None:
            return None
        try:
            if isinstance(image_source, bytes):
                pil_image = Image.open(io.BytesIO(image_source)).convert("RGB")
                rgb_frame = np.array(pil_image, dtype=np.uint8, copy=True)
                return np.ascontiguousarray(rgb_frame)

            if hasattr(image_source, "shape"):
                frame = np.array(image_source, dtype=np.uint8, copy=True)
                if frame.ndim == 3 and frame.shape[2] == 3:
                    if cv2 is not None:
                        try:
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        except Exception:
                            frame = frame[:, :, ::-1]
                    else:
                        frame = frame[:, :, ::-1]
                return np.ascontiguousarray(frame)
        except Exception as exc:
            logger.warning("face-service face_recognition_prepare_image_failed error=%s", exc)
            return None
        return None

    def _normalize_embedding(self, vector: list[float]):
        if np is None:
            raise RuntimeError("NumPy is required for face_recognition comparisons")
        target_length = min(len(vector), self.vector_dimensions)
        normalized = list(vector[:target_length])
        if target_length < self.vector_dimensions:
            normalized.extend([0.0] * (self.vector_dimensions - target_length))
        return np.asarray(normalized, dtype=np.float64)

    def _estimate_quality(self, *, image, face_location: tuple[int, int, int, int] | None) -> float:
        if np is None or face_location is None:
            return 0.9
        height = float(image.shape[0]) if getattr(image, "shape", None) is not None else 1.0
        width = float(image.shape[1]) if getattr(image, "shape", None) is not None else 1.0
        top, right, bottom, left = face_location
        face_area = max(1.0, float(max(0, right - left) * max(0, bottom - top)))
        image_area = max(1.0, width * height)
        ratio = min(1.0, face_area / image_area)
        return max(0.45, min(0.99, round(0.55 + ratio, 4)))
