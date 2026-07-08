import logging

from fastapi import FastAPI

from config import settings
from routes.faces import router as faces_router
from routes.system import router
from security import AuditLogMiddleware, AuthenticationMiddleware, RateLimitMiddleware
from services.face_recognition_service import FaceRecognitionService


app = FastAPI(title=settings.service_name, version=settings.service_version)
app.add_middleware(
    AuditLogMiddleware,
    service_name=settings.service_name,
    audit_enabled=settings.audit_enabled,
    audit_service_url=settings.audit_service_url,
    internal_audit_key=settings.audit_internal_key,
    excluded_paths={"/health", "/version"},
)
app.add_middleware(
    AuthenticationMiddleware,
    secret_key=settings.jwt_secret_key,
    issuer=settings.jwt_issuer,
    audience=settings.jwt_audience,
    public_paths={"/health", "/version", "/faces/config"} if settings.environment == "local" else {"/health", "/version"},
)
app.add_middleware(
    RateLimitMiddleware,
    limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
    excluded_paths={"/health", "/version"},
)
app.include_router(router)
app.include_router(faces_router)


@app.on_event("startup")
def log_face_runtime() -> None:
    capabilities = FaceRecognitionService().get_config()
    logging.getLogger(__name__).info(
        "face-service startup environment=%s mode=%s provider=%s app_name=%s app_root=%s opencv_available=%s insightface_available=%s face_recognition_available=%s provider_available=%s model_loaded=%s model_error=%s",
        settings.environment,
        capabilities.face_service_mode,
        capabilities.active_provider,
        settings.face_insightface_app_name,
        settings.face_insightface_root,
        capabilities.opencv_available,
        capabilities.insightface_available,
        capabilities.face_recognition_available,
        capabilities.provider_available,
        capabilities.model_loaded,
        capabilities.model_error,
    )
