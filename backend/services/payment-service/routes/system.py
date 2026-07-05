from fastapi import APIRouter

from config import settings
from schemas.system import HealthResponse, MockResponse, VersionResponse
from security import require_permissions
from services.mock_service import MockService


router = APIRouter()
mock_service = MockService()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        service=settings.service_name,
        status="ok",
        version=settings.service_version,
        environment=settings.environment,
    )


@router.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    return VersionResponse(service=settings.service_name, version=settings.service_version)


@router.get("/api/v1/mock", response_model=MockResponse, dependencies=[require_permissions("payments.read")])
def mock() -> MockResponse:
    return MockResponse(
        service=settings.service_name,
        resource="payment",
        data=mock_service.get_payload(),
    )
