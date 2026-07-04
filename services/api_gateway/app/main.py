from fastapi import FastAPI


app = FastAPI(title="API Gateway", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"service": "api_gateway", "status": "ok", "mode": "foundation"}


@app.get("/api/v1/catalog")
def catalog() -> dict:
    return {
        "project": "smart-campus-parking",
        "phase": "foundation",
        "services": [
            "auth_service",
            "identity_service",
            "parking_session_service",
            "payment_service",
            "facial_recognition_service",
            "plate_recognition_service",
            "liveness_service",
            "iot_service",
            "media_service",
        ],
    }
