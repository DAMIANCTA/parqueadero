from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from config import settings
from schemas.system import HealthResponse, MockResponse, VersionResponse
from security import require_permissions
from services.integration_service import IntegrationService
from services.mock_service import MockService


router = APIRouter()
mock_service = MockService()
integration_service = IntegrationService()


def _resolve_admin_portal_dir() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "web" / "admin-portal"
        if (candidate / "index.html").exists():
            return candidate
    return current.parents[1] / "web" / "admin-portal"


admin_portal_dir = _resolve_admin_portal_dir()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    checks = integration_service.collect_health()
    overall_status = (
        "ok"
        if all((check["status"] if isinstance(check, dict) else check.status) == "ok" for check in checks)
        else "degraded"
    )
    return HealthResponse(
        service=settings.service_name,
        status=overall_status,
        version=settings.service_version,
        environment=settings.environment,
        checks=checks,
    )


@router.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    return VersionResponse(service=settings.service_name, version=settings.service_version)


@router.get("/admin-portal", include_in_schema=False)
@router.get("/admin-portal/", include_in_schema=False)
def admin_portal_index() -> FileResponse:
    return FileResponse(admin_portal_dir / "index.html")


@router.get("/admin-portal/styles.css", include_in_schema=False)
def admin_portal_styles() -> FileResponse:
    return FileResponse(admin_portal_dir / "styles.css", media_type="text/css")


@router.get("/admin-portal/app.js", include_in_schema=False)
def admin_portal_app() -> FileResponse:
    return FileResponse(admin_portal_dir / "app.js", media_type="application/javascript")


@router.get("/api/v1/mock", response_model=MockResponse, dependencies=[require_permissions("gateway.catalog.read")])
def mock() -> MockResponse:
    return MockResponse(
        service=settings.service_name,
        resource="service-catalog",
        data=mock_service.get_payload(),
    )
