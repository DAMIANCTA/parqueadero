from fastapi import FastAPI


app = FastAPI(title="Identity Service", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"service": "identity_service", "status": "ok", "mode": "mock"}


@app.get("/api/v1/plates/{plate}")
def get_plate(plate: str) -> dict:
    return {
        "plate": plate.upper(),
        "authorized_people": [
            {
                "person_id": "person-001",
                "full_name": "Maria Perez",
                "role": "student",
                "active_permission": True,
            }
        ],
    }


@app.get("/api/v1/people/{person_id}")
def get_person(person_id: str) -> dict:
    return {
        "person_id": person_id,
        "full_name": "Maria Perez",
        "institution_role": "student",
        "status": "active",
    }
