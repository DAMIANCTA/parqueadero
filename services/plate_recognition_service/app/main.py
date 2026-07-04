from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Plate Recognition Service", version="0.1.0")


class PlateDetectionRequest(BaseModel):
    image_uri: str
    country_code: str = "EC"


@app.get("/health")
def health() -> dict:
    return {"service": "plate_recognition_service", "status": "ok", "mode": "mock"}


@app.post("/api/v1/plates/detect")
def detect_plate(payload: PlateDetectionRequest) -> dict:
    return {
        "image_uri": payload.image_uri,
        "plate": "ABC1234",
        "confidence": 0.97,
        "country_code": payload.country_code,
    }
