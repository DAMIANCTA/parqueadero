from fastapi import FastAPI


app = FastAPI(title="Payment Service", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"service": "payment_service", "status": "ok", "mode": "mock"}


@app.get("/api/v1/payments/sessions/{session_id}/status")
def payment_status(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "payment_status": "paid",
        "currency": "USD",
        "amount": 1.50,
    }
