from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Facial Recognition Service", version="0.1.0")


class FaceVerifyRequest(BaseModel):
    subject_id: str | None = None
    entry_face_reference: str
    exit_face_reference: str


@app.get("/health")
def health() -> dict:
    return {"service": "facial_recognition_service", "status": "ok", "mode": "mock"}


@app.post("/api/v1/faces/verify")
def verify_face(payload: FaceVerifyRequest) -> dict:
    return {
        "subject_id": payload.subject_id,
        "match": True,
        "similarity_score": 0.98,
        "provider": "mock-engine",
    }
