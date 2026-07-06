from fastapi import APIRouter

from config import settings
from schemas.system import HealthResponse, MockResponse, VersionResponse
from security import require_permissions
from services.integration_service import IntegrationService
from services.mock_service import MockService


router = APIRouter()
mock_service = MockService()
integration_service = IntegrationService()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    checks = integration_service.collect_health()
    overall_status = "ok" if all(check.status == "ok" for check in checks) else "degraded"
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


@router.get("/api/v1/mock", response_model=MockResponse, dependencies=[require_permissions("gateway.catalog.read")])
def mock() -> MockResponse:
    return MockResponse(
        service=settings.service_name,
        resource="service-catalog",
        data=mock_service.get_payload(),
    )
