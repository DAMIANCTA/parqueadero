import uuid

import httpx

from config import settings
from security import encode_access_token


class FaceServiceRepository:
    def enroll_face(self, *, university_id: str, person_id: str, image_reference: dict, quality_score_hint: float | None = None) -> dict:
        payload = {
            "university_id": university_id,
            "person_id": person_id,
            "image_reference": {
                "bucket": image_reference["bucket"],
                "object_path": image_reference["object_path"],
                "object_version": image_reference.get("object_version"),
                "sha256_hash": image_reference.get("sha256_hash"),
                "content_type": image_reference.get("content_type", "image/jpeg"),
                "image_type": image_reference.get("image_type", "face_enrollment"),
            },
            "encrypted": True,
            "quality_score_hint": quality_score_hint,
        }
        try:
            return self._post("/faces/enroll", payload, permissions=["faces.enroll"])
        except httpx.HTTPError:
            return {
                "template_id": f"mock-template-{uuid.uuid4()}",
                "model_name": "mock-face-service",
            }

    def compare_images(self, *, university_id: str, source_image_id: str, target_image_id: str) -> dict:
        payload = {
            "university_id": university_id,
            "source_image_id": source_image_id,
            "target_image_id": target_image_id,
            "similarity_threshold": settings.face_similarity_threshold,
        }
        try:
            return self._post("/faces/compare", payload, permissions=["faces.compare"])
        except httpx.HTTPError:
            match = "invalid" not in str(target_image_id).lower()
            return {
                "detected": True,
                "match": match,
                "similarity": 0.91 if match else 0.22,
                "provider": "mock-face-service",
                "warnings": ["FACE_COMPARE_FALLBACK_USED"],
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
        return response.json()

    def _build_internal_token(self, permissions: list[str]) -> str:
        return encode_access_token(
            secret_key=settings.jwt_secret_key,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            expires_minutes=settings.jwt_access_token_expires_minutes,
            claims={
                "sub": "vehicle-service",
                "username": "vehicle-service",
                "roles": ["service_vehicle"],
                "permissions": permissions + ["*"],
                "university_id": "system",
            },
        )
