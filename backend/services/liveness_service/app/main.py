from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Liveness Service", version="0.1.0")


class LivenessRequest(BaseModel):
    face_image_uri: str
    challenge_type: str = "blink"


@app.get("/health")
def health() -> dict:
    return {"service": "liveness_service", "status": "ok", "mode": "mock"}


@app.post("/api/v1/liveness/check")
def check_liveness(payload: LivenessRequest) -> dict:
    return {
        "face_image_uri": payload.face_image_uri,
        "liveness_passed": True,
        "score": 0.99,
        "challenge_type": payload.challenge_type,
    }
