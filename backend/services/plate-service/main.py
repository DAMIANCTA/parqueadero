from fastapi import FastAPI

from config import settings
from routes.plates import router as plates_router
from routes.system import router
from security import AuditLogMiddleware, AuthenticationMiddleware, RateLimitMiddleware


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
    public_paths={"/health", "/version"},
)
app.add_middleware(
    RateLimitMiddleware,
    limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
    excluded_paths={"/health", "/version"},
)
app.include_router(router)
app.include_router(plates_router)
