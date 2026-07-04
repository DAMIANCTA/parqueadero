from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Auth Service", version="0.1.0")


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health() -> dict:
    return {"service": "auth_service", "status": "ok", "mode": "mock"}


@app.post("/api/v1/auth/token")
def issue_token(payload: LoginRequest) -> dict:
    return {
        "access_token": f"mock-token-for-{payload.username}",
        "token_type": "bearer",
        "roles": ["operator"],
    }
