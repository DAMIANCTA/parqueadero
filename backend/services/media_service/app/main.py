from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Media Service", version="0.1.0")


class PresignUploadRequest(BaseModel):
    object_name: str
    content_type: str
    category: str


@app.get("/health")
def health() -> dict:
    return {"service": "media_service", "status": "ok", "mode": "mock"}


@app.post("/api/v1/media/presign-upload")
def presign_upload(payload: PresignUploadRequest) -> dict:
    return {
        "object_name": payload.object_name,
        "category": payload.category,
        "upload_url": f"https://mock-minio.local/upload/{payload.object_name}",
        "content_type": payload.content_type,
    }
