from fastapi import APIRouter, HTTPException

from schemas.iot import (
    GateActionRequest,
    GateCommandResponse,
    GateRuntimeStatusResponse,
    LegacyGateOpenRequest,
    LegacyGateOpenResponse,
    LegacyGateStatusRequest,
    LegacyGateStatusResponse,
)
from security import require_permissions
from services.mqtt_service import MqttService


router = APIRouter(tags=["iot"])
mqtt_service = MqttService()


@router.post("/gates/{gate_id}/open", response_model=GateCommandResponse, dependencies=[require_permissions("iot.gates.open")])
def open_gate(gate_id: str, command: GateActionRequest) -> GateCommandResponse:
    try:
        payload = mqtt_service.open_gate(gate_id, command)
    except Exception as exc:  # pragma: no cover - defensive error translation
        raise HTTPException(status_code=503, detail=f"MQTT publish failed: {exc}") from exc
    return GateCommandResponse(**payload)


@router.post("/gates/{gate_id}/deny", response_model=GateCommandResponse, dependencies=[require_permissions("iot.gates.deny")])
def deny_gate(gate_id: str, command: GateActionRequest) -> GateCommandResponse:
    try:
        payload = mqtt_service.deny_gate(gate_id, command)
    except Exception as exc:  # pragma: no cover - defensive error translation
        raise HTTPException(status_code=503, detail=f"MQTT deny publish failed: {exc}") from exc
    return GateCommandResponse(**payload)


@router.get("/gates/{gate_id}/status", response_model=GateRuntimeStatusResponse, dependencies=[require_permissions("iot.gates.read")])
def gate_status(gate_id: str) -> GateRuntimeStatusResponse:
    try:
        payload = mqtt_service.get_gate_status(gate_id)
    except Exception as exc:  # pragma: no cover - defensive error translation
        raise HTTPException(status_code=503, detail=f"MQTT status unavailable: {exc}") from exc
    return GateRuntimeStatusResponse(**payload)


@router.post("/api/v1/gates/open", response_model=LegacyGateOpenResponse, dependencies=[require_permissions("iot.gates.open")])
def legacy_open_gate(command: LegacyGateOpenRequest) -> LegacyGateOpenResponse:
    try:
        payload = mqtt_service.publish_legacy_open(command)
    except Exception as exc:  # pragma: no cover - defensive error translation
        raise HTTPException(status_code=503, detail=f"MQTT publish failed: {exc}") from exc
    return LegacyGateOpenResponse(**payload)


@router.post("/api/v1/gates/status", response_model=LegacyGateStatusResponse, dependencies=[require_permissions("iot.gates.open")])
def legacy_status(status: LegacyGateStatusRequest) -> LegacyGateStatusResponse:
    try:
        payload = mqtt_service.publish_legacy_status(status)
    except Exception as exc:  # pragma: no cover - defensive error translation
        raise HTTPException(status_code=503, detail=f"MQTT status publish failed: {exc}") from exc
    return LegacyGateStatusResponse(**payload)
