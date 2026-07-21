from fastapi import APIRouter, Query

from repositories.parking_session_repository import ParkingSessionRepository
from schemas.parking import (
    ActiveSessionResponse,
    ParkingEntryRequest,
    ParkingEntryResponse,
    ParkingExitRequest,
    ParkingExitResponse,
    ParkingHistoryResponse,
)
from security import require_permissions
from services.exit_service import ExitService
from services.entry_service import EntryService


router = APIRouter(prefix="/parking", tags=["parking"])
entry_service = EntryService()
exit_service = ExitService()
parking_session_repository = ParkingSessionRepository()


@router.post("/entry", response_model=ParkingEntryResponse, dependencies=[require_permissions("parking.entry")])
def create_entry(payload: ParkingEntryRequest) -> ParkingEntryResponse:
    return entry_service.process_entry(payload)


@router.post("/exit", response_model=ParkingExitResponse, dependencies=[require_permissions("parking.exit")])
def create_exit(payload: ParkingExitRequest) -> ParkingExitResponse:
    return exit_service.process_exit(payload)


@router.get(
    "/active-session/{plate_text}",
    response_model=ActiveSessionResponse,
    dependencies=[require_permissions("parking.entry")],
)
def get_active_session(plate_text: str) -> ActiveSessionResponse:
    normalized_plate = plate_text.strip().upper().replace(" ", "").replace("-", "")
    active = parking_session_repository.has_active_session_by_plate(normalized_plate)
    return ActiveSessionResponse(plate_text=normalized_plate, active=active)


@router.get(
    "/history",
    response_model=ParkingHistoryResponse,
    dependencies=[require_permissions("parking.entry")],
)
def get_history(university_id: str | None = Query(default=None), limit: int = Query(default=100, le=500)) -> ParkingHistoryResponse:
    items = parking_session_repository.list_history(university_id=university_id, limit=limit)
    return ParkingHistoryResponse(total=len(items), items=items)
