from fastapi import FastAPI

from config import settings
from security import AuditLogMiddleware, AuthenticationMiddleware, RateLimitMiddleware
from routes.system import router


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
