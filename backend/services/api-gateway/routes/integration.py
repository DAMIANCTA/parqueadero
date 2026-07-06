from fastapi import APIRouter, HTTPException
import httpx

from schemas.integration import (
    DemoOpenGateRequest,
    DemoOpenGateResponse,
    ParkingAuthorizationResponse,
    ParkingEntryRequest,
    ParkingExitRequest,
)
from services.integration_service import IntegrationService


router = APIRouter(tags=["integration"])
integration_service = IntegrationService()


@router.post("/parking/entry", response_model=ParkingAuthorizationResponse)
def gateway_entry(payload: ParkingEntryRequest) -> ParkingAuthorizationResponse:
    try:
        response = integration_service.proxy_entry(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Parking service unavailable: {exc}") from exc
    return ParkingAuthorizationResponse(**response)


@router.post("/parking/exit", response_model=ParkingAuthorizationResponse)
def gateway_exit(payload: ParkingExitRequest) -> ParkingAuthorizationResponse:
    try:
        response = integration_service.proxy_exit(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Parking service unavailable: {exc}") from exc
    return ParkingAuthorizationResponse(**response)


@router.post("/demo/open-gate", response_model=DemoOpenGateResponse)
def demo_open_gate(payload: DemoOpenGateRequest) -> DemoOpenGateResponse:
    try:
        response = integration_service.open_demo_gate(payload)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"IoT service unavailable: {exc}") from exc
    return DemoOpenGateResponse(**response)
