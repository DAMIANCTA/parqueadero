import logging

from fastapi import FastAPI

from config import settings
from routes.plates import router as plates_router
from routes.system import router
from security import AuditLogMiddleware, AuthenticationMiddleware, RateLimitMiddleware
from services.runtime_probe import probe_runtime_capabilities


app = FastAPI(title=settings.service_name, version=settings.service_version)
logger = logging.getLogger(__name__)
public_paths = {"/health", "/version"}
if settings.environment == "local":
    public_paths.add("/plates/config")

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
    public_paths=public_paths,
)
app.add_middleware(
    RateLimitMiddleware,
    limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
    excluded_paths={"/health", "/version"},
)
app.include_router(router)
app.include_router(plates_router)


@app.on_event("startup")
async def log_runtime_configuration() -> None:
    capabilities = probe_runtime_capabilities()
    logger.info(
        "plate-service startup environment=%s plate_service_mode=%s plate_detection_mode=%s model_path=%s model_exists=%s",
        capabilities.environment,
        capabilities.plate_service_mode,
        capabilities.plate_detection_mode,
        capabilities.model_path,
        capabilities.model_exists,
    )
    logger.info(
        "plate-service runtime opencv_available=%s easyocr_available=%s rapidocr_available=%s paddleocr_available=%s selected_ocr_engine=%s",
        capabilities.opencv_available,
        capabilities.easyocr_available,
        capabilities.rapidocr_available,
        capabilities.paddleocr_available,
        capabilities.ocr_engine,
    )
    if capabilities.errors:
        for component, error in capabilities.errors.items():
            logger.warning("plate-service runtime dependency_unavailable component=%s error=%s", component, error)
