from repositories.face_repository import FaceRepository


class FaceValidationService:
    def __init__(self) -> None:
        self.repository = FaceRepository()

    def validate_entry_face(self, face_image_id: str, confidence_face: float, min_confidence: float) -> dict:
        return self.repository.validate(face_image_id, confidence_face, min_confidence)

    def validate_registered_face(self, face_image_id: str, confidence_face: float, min_confidence: float) -> dict:
        return self.repository.validate(face_image_id, confidence_face, min_confidence)

    def compare_entry_and_exit_faces(
        self,
        entry_face_image_id: str,
        exit_face_image_id: str,
        confidence_face: float,
        min_confidence: float,
    ) -> dict:
        return self.repository.compare(entry_face_image_id, exit_face_image_id, confidence_face, min_confidence)
