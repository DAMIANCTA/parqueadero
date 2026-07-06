from fastapi import APIRouter, HTTPException

from schemas.iot import GateOpenRequest, GateOpenResponse, GateStatusRequest, GateStatusResponse
from security import require_permissions
from services.mqtt_service import MqttService


router = APIRouter(prefix="/api/v1/gates", tags=["iot"])
mqtt_service = MqttService()


@router.post("/open", response_model=GateOpenResponse, dependencies=[require_permissions("iot.gates.open")])
def open_gate(command: GateOpenRequest) -> GateOpenResponse:
    try:
        payload = mqtt_service.publish_gate_open(command)
    except Exception as exc:  # pragma: no cover - defensive error translation
        raise HTTPException(status_code=503, detail=f"MQTT publish failed: {exc}") from exc
    return GateOpenResponse(**payload)


@router.post("/status", response_model=GateStatusResponse, dependencies=[require_permissions("iot.gates.open")])
def report_gate_status(status: GateStatusRequest) -> GateStatusResponse:
    try:
        payload = mqtt_service.publish_gate_status(status)
    except Exception as exc:  # pragma: no cover - defensive error translation
        raise HTTPException(status_code=503, detail=f"MQTT status publish failed: {exc}") from exc
    return GateStatusResponse(**payload)
