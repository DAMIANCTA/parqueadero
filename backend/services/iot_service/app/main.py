from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="IoT Service", version="0.1.0")


class GateOpenRequest(BaseModel):
    reason: str
    session_id: str | None = None
    plate: str | None = None


@app.get("/health")
def health() -> dict:
    return {"service": "iot_service", "status": "ok", "mode": "mock"}


@app.post("/api/v1/gates/{gate_id}/open")
def open_gate(gate_id: str, payload: GateOpenRequest) -> dict:
    return {
        "gate_id": gate_id,
        "command": "open",
        "published": True,
        "reason": payload.reason,
        "session_id": payload.session_id,
        "plate": payload.plate,
    }
