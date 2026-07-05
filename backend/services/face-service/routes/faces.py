from fastapi import APIRouter

from schemas.faces import (
    FaceCompareRequest,
    FaceCompareResponse,
    FaceEnrollRequest,
    FaceEnrollResponse,
    FaceLivenessCheckRequest,
    FaceLivenessCheckResponse,
    FaceVerifyRequest,
    FaceVerifyResponse,
)
from security import require_permissions
from services.face_recognition_service import FaceRecognitionService


router = APIRouter(tags=["faces"])
face_service = FaceRecognitionService()


@router.post("/faces/enroll", response_model=FaceEnrollResponse, dependencies=[require_permissions("faces.enroll")])
def enroll_face(payload: FaceEnrollRequest) -> FaceEnrollResponse:
    return face_service.enroll(payload)


@router.post("/faces/verify", response_model=FaceVerifyResponse, dependencies=[require_permissions("faces.verify")])
def verify_face(payload: FaceVerifyRequest) -> FaceVerifyResponse:
    return face_service.verify(payload)


@router.post("/faces/compare", response_model=FaceCompareResponse, dependencies=[require_permissions("faces.compare")])
def compare_faces(payload: FaceCompareRequest) -> FaceCompareResponse:
    return face_service.compare(payload)


@router.post("/faces/liveness-check", response_model=FaceLivenessCheckResponse, dependencies=[require_permissions("faces.liveness_check")])
def liveness_check(payload: FaceLivenessCheckRequest) -> FaceLivenessCheckResponse:
    return face_service.liveness_check(payload)
