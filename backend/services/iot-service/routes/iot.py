from fastapi import APIRouter, HTTPException

from schemas.iot import GateOpenRequest, GateOpenResponse
from services.mqtt_service import MqttService


router = APIRouter(prefix="/api/v1/gates", tags=["iot"])
mqtt_service = MqttService()


@router.post("/open", response_model=GateOpenResponse)
def open_gate(command: GateOpenRequest) -> GateOpenResponse:
    try:
        payload = mqtt_service.publish_gate_open(command)
    except Exception as exc:  # pragma: no cover - defensive error translation
        raise HTTPException(status_code=503, detail=f"MQTT publish failed: {exc}") from exc
    return GateOpenResponse(**payload)
