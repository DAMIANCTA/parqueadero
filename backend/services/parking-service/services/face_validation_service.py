from repositories.face_repository import FaceRepository


class FaceValidationService:
    def __init__(self) -> None:
        self.repository = FaceRepository()

    def validate_entry_face(
        self,
        *,
        university_id: str,
        session_id: str,
        face_image_id: str,
        confidence_face: float,
        min_confidence: float,
    ) -> dict:
        return self.repository.detect_for_session(
            university_id=university_id,
            session_id=session_id,
            face_image_id=face_image_id,
            confidence_face=confidence_face,
            min_confidence=min_confidence,
        )

    def validate_registered_face(
        self,
        *,
        university_id: str,
        face_image_id: str,
        confidence_face: float,
        min_confidence: float,
    ) -> dict:
        return self.repository.validate_direct_capture(
            university_id=university_id,
            face_image_id=face_image_id,
            confidence_face=confidence_face,
            min_confidence=min_confidence,
        )

    def verify_session_face(
        self,
        *,
        university_id: str,
        session_id: str,
        face_image_id: str,
        gate_id: str,
        confidence_face: float,
        min_confidence: float,
    ) -> dict:
        return self.repository.verify_session(
            university_id=university_id,
            session_id=session_id,
            face_image_id=face_image_id,
            gate_id=gate_id,
            confidence_face=confidence_face,
            min_confidence=min_confidence,
        )
