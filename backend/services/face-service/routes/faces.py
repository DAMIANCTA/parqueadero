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
from services.face_recognition_service import FaceRecognitionService


router = APIRouter(tags=["faces"])
face_service = FaceRecognitionService()


@router.post("/faces/enroll", response_model=FaceEnrollResponse)
def enroll_face(payload: FaceEnrollRequest) -> FaceEnrollResponse:
    return face_service.enroll(payload)


@router.post("/faces/verify", response_model=FaceVerifyResponse)
def verify_face(payload: FaceVerifyRequest) -> FaceVerifyResponse:
    return face_service.verify(payload)


@router.post("/faces/compare", response_model=FaceCompareResponse)
def compare_faces(payload: FaceCompareRequest) -> FaceCompareResponse:
    return face_service.compare(payload)


@router.post("/faces/liveness-check", response_model=FaceLivenessCheckResponse)
def liveness_check(payload: FaceLivenessCheckRequest) -> FaceLivenessCheckResponse:
    return face_service.liveness_check(payload)
