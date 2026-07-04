from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Parking Session Service", version="0.1.0")


class EntryRequest(BaseModel):
    university_id: str
    campus_id: str
    gate_id: str
    plate: str
    face_reference: str
    actor_type: str


class ExitCheckRequest(BaseModel):
    session_id: str
    plate: str
    face_reference: str
    payment_confirmed: bool = False


@app.get("/health")
def health() -> dict:
    return {"service": "parking_session_service", "status": "ok", "mode": "mock"}


@app.post("/api/v1/sessions/entry")
def create_entry(payload: EntryRequest) -> dict:
    return {
        "session_id": "session-mock-001",
        "status": "entry_authorized",
        "plate": payload.plate.upper(),
        "gate_id": payload.gate_id,
        "actor_type": payload.actor_type,
    }


@app.post("/api/v1/sessions/exit-check")
def validate_exit(payload: ExitCheckRequest) -> dict:
    return {
        "session_id": payload.session_id,
        "exit_authorized": payload.payment_confirmed,
        "checks": {
            "plate_match": True,
            "face_match": True,
            "payment_confirmed": payload.payment_confirmed,
        },
    }
