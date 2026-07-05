class FaceRepository:
    def validate(self, face_image_id: str, confidence_face: float, min_confidence: float) -> dict:
        return {
            "face_image_id": face_image_id,
            "accepted": confidence_face >= min_confidence,
            "confidence_face": confidence_face,
            "provider": "mock-face-service",
        }

    def compare(
        self,
        entry_face_image_id: str,
        exit_face_image_id: str,
        confidence_face: float,
        min_confidence: float,
    ) -> dict:
        accepted = (
            confidence_face >= min_confidence
            and self._extract_identity(entry_face_image_id) == self._extract_identity(exit_face_image_id)
        )
        return {
            "accepted": accepted,
            "entry_face_image_id": entry_face_image_id,
            "exit_face_image_id": exit_face_image_id,
            "confidence_face": confidence_face,
            "provider": "mock-face-service",
        }

    def _extract_identity(self, face_image_id: str) -> str:
        return face_image_id.split("-")[-1]
