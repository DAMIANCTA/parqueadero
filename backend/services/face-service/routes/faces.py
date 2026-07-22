from fastapi import APIRouter, File, UploadFile

from schemas.faces import (
    FaceCompareRequest,
    FaceCompareResponse,
    FaceConfigResponse,
    FaceDetectRequest,
    FaceDetectResponse,
    FaceEnrollRequest,
    FaceEnrollResponse,
    FaceLiveCheckResponse,
    FaceLivenessRequest,
    FaceLivenessResponse,
    FaceLivenessCheckRequest,
    FaceLivenessCheckResponse,
    FaceVerifyRequest,
    FaceVerifyResponse,
    FaceVerifySessionRequest,
    FaceVerifySessionResponse,
)
from security import require_permissions
from services.face_recognition_service import FaceRecognitionService


router = APIRouter(tags=["faces"])
face_service = FaceRecognitionService()


@router.get("/faces/config", response_model=FaceConfigResponse)
def faces_config() -> FaceConfigResponse:
    return face_service.get_config()


@router.post("/faces/detect", response_model=FaceDetectResponse, dependencies=[require_permissions("faces.verify")])
def detect_face(payload: FaceDetectRequest) -> FaceDetectResponse:
    return face_service.detect(payload)


@router.post("/faces/enroll", response_model=FaceEnrollResponse, dependencies=[require_permissions("faces.enroll")])
def enroll_face(payload: FaceEnrollRequest) -> FaceEnrollResponse:
    return face_service.enroll(payload)


@router.post("/faces/detect-live", response_model=FaceLiveCheckResponse, dependencies=[require_permissions("faces.verify")])
async def detect_face_live(file: UploadFile = File(...)) -> FaceLiveCheckResponse:
    return face_service.detect_live(await file.read())


@router.post("/faces/verify", response_model=FaceVerifyResponse, dependencies=[require_permissions("faces.verify")])
def verify_face(payload: FaceVerifyRequest) -> FaceVerifyResponse:
    return face_service.verify(payload)


@router.post("/faces/compare", response_model=FaceCompareResponse, dependencies=[require_permissions("faces.compare")])
def compare_faces(payload: FaceCompareRequest) -> FaceCompareResponse:
    return face_service.compare(payload)


@router.post("/faces/verify-session", response_model=FaceVerifySessionResponse, dependencies=[require_permissions("faces.verify")])
def verify_session_face(payload: FaceVerifySessionRequest) -> FaceVerifySessionResponse:
    return face_service.verify_session(payload)


@router.post("/faces/liveness", response_model=FaceLivenessResponse, dependencies=[require_permissions("faces.liveness_check")])
def liveness(payload: FaceLivenessRequest) -> FaceLivenessResponse:
    return face_service.liveness(payload)


@router.post("/faces/liveness-check", response_model=FaceLivenessCheckResponse, dependencies=[require_permissions("faces.liveness_check")])
def liveness_check(payload: FaceLivenessCheckRequest) -> FaceLivenessCheckResponse:
    return face_service.liveness_check(payload)
