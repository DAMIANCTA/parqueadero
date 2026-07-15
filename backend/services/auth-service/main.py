from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routes.auth import router as auth_router
from routes.system import router as system_router
from security import AuditLogMiddleware, AuthenticationMiddleware, RateLimitMiddleware


app = FastAPI(title=settings.service_name, version=settings.service_version)
allow_origins = settings.cors_allow_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials="*" not in allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
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
    public_paths={
        "/health",
        "/version",
        "/auth/login",
        "/api/v1/auth/login",
        "/auth/token",
        "/api/v1/auth/token",
    },
)
app.add_middleware(
    RateLimitMiddleware,
    limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
    excluded_paths={"/health", "/version"},
)
app.include_router(system_router)
app.include_router(auth_router)
