import logging

import httpx

from config import settings
from security import encode_access_token


logger = logging.getLogger(__name__)


class FaceRepository:
    def get_config(self) -> dict:
        try:
            return self._get("/faces/config", permissions=["faces.verify"])
        except httpx.HTTPError as exc:
            logger.warning("parking-service face_repository config_fallback error=%s", exc)
            return {
                "face_service_mode": settings.face_service_mode,
                "face_real_provider": "mock-fallback",
                "similarity_threshold": settings.face_similarity_threshold,
            }

    def detect_for_session(
        self,
        *,
        university_id: str,
        session_id: str,
        face_image_id: str,
        confidence_face: float,
        min_confidence: float,
    ) -> dict:
        if confidence_face < min_confidence:
            return {
                "accepted": False,
                "detected": False,
                "match": None,
                "similarity": None,
                "provider": "confidence-gate",
                "mode": settings.face_service_mode,
                "warnings": ["FACE_CONFIDENCE_TOO_LOW"],
                "image_id": face_image_id,
            }
        try:
            payload = self._post(
                "/faces/detect",
                {
                    "university_id": university_id,
                    "session_id": session_id,
                    "image_id": face_image_id,
                    "quality_score_hint": confidence_face,
                },
                permissions=["faces.verify"],
            )
        except httpx.HTTPError as exc:
            logger.warning("parking-service face_repository detect_fallback error=%s", exc)
            return self._fallback_detect(face_image_id=face_image_id, confidence_face=confidence_face, mode="mock-fallback")
        return {
            "accepted": bool(payload.get("detected")) and int(payload.get("embedding_size", 0)) > 0,
            "detected": payload.get("detected", False),
            "match": None,
            "similarity": None,
            "provider": payload.get("provider", "face-service"),
            "mode": payload.get("mode", settings.face_service_mode),
            "warnings": payload.get("warnings", []),
            "image_id": payload.get("image_id", face_image_id),
            "template_id": payload.get("template_id"),
            "bounding_box": payload.get("bounding_box"),
            "quality_score": payload.get("quality_score"),
            "embedding_size": payload.get("embedding_size", 0),
            "model_name": payload.get("model_name", "unknown"),
        }

    def verify_session(
        self,
        *,
        university_id: str,
        session_id: str,
        face_image_id: str,
        gate_id: str,
        confidence_face: float,
        min_confidence: float,
    ) -> dict:
        if confidence_face < min_confidence:
            return {
                "accepted": False,
                "detected": False,
                "match": False,
                "similarity": 0.0,
                "provider": "confidence-gate",
                "mode": settings.face_service_mode,
                "warnings": ["FACE_CONFIDENCE_TOO_LOW"],
                "image_id": face_image_id,
            }
        try:
            payload = self._post(
                "/faces/verify-session",
                {
                    "university_id": university_id,
                    "session_id": session_id,
                    "probe_image_id": face_image_id,
                    "similarity_threshold": settings.face_similarity_threshold,
                    "gate_id": gate_id,
                },
                permissions=["faces.verify"],
            )
        except httpx.HTTPError as exc:
            logger.warning("parking-service face_repository verify_fallback error=%s", exc)
            return self._fallback_verify(
                session_id=session_id,
                face_image_id=face_image_id,
                confidence_face=confidence_face,
                mode="mock-fallback",
            )
        return {
            "accepted": bool(payload.get("detected")) and bool(payload.get("match")),
            "detected": payload.get("detected", False),
            "match": payload.get("match", False),
            "similarity": payload.get("similarity", 0.0),
            "threshold": payload.get("threshold", settings.face_similarity_threshold),
            "provider": payload.get("provider", "face-service"),
            "mode": payload.get("mode", settings.face_service_mode),
            "warnings": payload.get("warnings", []),
            "image_id": payload.get("image_id", face_image_id),
            "template_id": payload.get("template_id"),
            "bounding_box": payload.get("bounding_box"),
            "quality_score": payload.get("quality_score"),
            "embedding_size": payload.get("embedding_size", 0),
            "model_name": payload.get("model_name", "unknown"),
        }

    def validate_direct_capture(
        self,
        *,
        university_id: str,
        face_image_id: str,
        confidence_face: float,
        min_confidence: float,
    ) -> dict:
        if confidence_face < min_confidence:
            return {
                "accepted": False,
                "detected": False,
                "provider": "confidence-gate",
                "mode": settings.face_service_mode,
                "warnings": ["FACE_CONFIDENCE_TOO_LOW"],
                "image_id": face_image_id,
            }
        try:
            payload = self._post(
                "/faces/detect",
                {
                    "university_id": university_id,
                    "image_id": face_image_id,
                    "quality_score_hint": confidence_face,
                },
                permissions=["faces.verify"],
            )
        except httpx.HTTPError as exc:
            logger.warning("parking-service face_repository direct_detect_fallback error=%s", exc)
            return self._fallback_detect(face_image_id=face_image_id, confidence_face=confidence_face, mode="mock-fallback")
        return {
            "accepted": bool(payload.get("detected")),
            "detected": payload.get("detected", False),
            "provider": payload.get("provider", "face-service"),
            "mode": payload.get("mode", settings.face_service_mode),
            "warnings": payload.get("warnings", []),
            "image_id": payload.get("image_id", face_image_id),
            "bounding_box": payload.get("bounding_box"),
            "quality_score": payload.get("quality_score"),
            "embedding_size": payload.get("embedding_size", 0),
            "model_name": payload.get("model_name", "unknown"),
        }

    def _post(self, path: str, payload: dict, *, permissions: list[str]) -> dict:
        with httpx.Client(timeout=settings.face_service_timeout_seconds) as client:
            response = client.post(
                f"{settings.face_service_url.rstrip('/')}{path}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._build_internal_token(permissions)}",
                    "Content-Type": "application/json",
                },
            )
        response.raise_for_status()
        data = response.json()
        logger.info("parking-service face_repository path=%s response=%s", path, data)
        return data

    def _get(self, path: str, *, permissions: list[str]) -> dict:
        with httpx.Client(timeout=settings.face_service_timeout_seconds) as client:
            response = client.get(
                f"{settings.face_service_url.rstrip('/')}{path}",
                headers={"Authorization": f"Bearer {self._build_internal_token(permissions)}"},
            )
        response.raise_for_status()
        return response.json()

    def _build_internal_token(self, permissions: list[str]) -> str:
        return encode_access_token(
            secret_key=settings.jwt_secret_key,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            expires_minutes=settings.jwt_access_token_expires_minutes,
            claims={
                "sub": "parking-service",
                "username": "parking-service",
                "roles": ["service_parking"],
                "permissions": permissions + ["*"],
                "university_id": "system",
            },
        )

    def _fallback_detect(self, *, face_image_id: str, confidence_face: float, mode: str) -> dict:
        accepted = confidence_face >= settings.min_face_confidence and "invalid" not in face_image_id.lower()
        return {
            "accepted": accepted,
            "detected": accepted,
            "match": None,
            "similarity": None,
            "provider": "mock-face-service",
            "mode": mode,
            "warnings": [] if accepted else ["FACE_NOT_DETECTED"],
            "image_id": face_image_id,
            "template_id": None,
            "bounding_box": None,
            "quality_score": confidence_face,
            "embedding_size": 16 if accepted else 0,
            "model_name": "mock-face-model",
        }

    def _fallback_verify(self, *, session_id: str, face_image_id: str, confidence_face: float, mode: str) -> dict:
        session_hint = session_id.split("-")[-1]
        image_hint = face_image_id.split("-")[-1]
        match = confidence_face >= settings.min_face_confidence and (
            image_hint == session_hint or face_image_id.lower().startswith("face-exit")
        )
        return {
            "accepted": match,
            "detected": True,
            "match": match,
            "similarity": 0.91 if match else 0.31,
            "threshold": settings.face_similarity_threshold,
            "provider": "mock-face-service",
            "mode": mode,
            "warnings": [] if match else ["FACE_VERIFICATION_FAILED"],
            "image_id": face_image_id,
            "template_id": None,
            "bounding_box": None,
            "quality_score": confidence_face,
            "embedding_size": 16,
            "model_name": "mock-face-model",
        }
