from fastapi import APIRouter

from config import settings
from schemas.system import HealthResponse, MockResponse, PlateConfigResponse, VersionResponse
from security import require_permissions
from services.mock_service import MockService
from services.runtime_probe import probe_runtime_capabilities


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


@router.get("/plates/config", response_model=PlateConfigResponse)
def plate_config() -> PlateConfigResponse:
    capabilities = probe_runtime_capabilities()
    return PlateConfigResponse(
        environment=capabilities.environment,
        plate_service_mode=capabilities.plate_service_mode,
        plate_detection_mode=capabilities.plate_detection_mode,
        opencv_available=capabilities.opencv_available,
        easyocr_available=capabilities.easyocr_available,
        rapidocr_available=capabilities.rapidocr_available,
        paddleocr_available=capabilities.paddleocr_available,
        ocr_engine=capabilities.ocr_engine,
        model_path=capabilities.model_path,
        model_exists=capabilities.model_exists,
        min_confidence=capabilities.min_confidence,
    )


@router.get("/api/v1/mock", response_model=MockResponse, dependencies=[require_permissions("plates.detect")])
def mock() -> MockResponse:
    return MockResponse(
        service=settings.service_name,
        resource="plate-detection",
        data=mock_service.get_payload(),
    )
