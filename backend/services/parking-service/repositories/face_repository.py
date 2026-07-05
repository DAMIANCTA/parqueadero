class FaceRepository:
    def validate(self, face_image_id: str, confidence_face: float, min_confidence: float) -> dict:
        return {
            "face_image_id": face_image_id,
            "accepted": confidence_face >= min_confidence,
            "confidence_face": confidence_face,
            "provider": "mock-face-service",
        }
