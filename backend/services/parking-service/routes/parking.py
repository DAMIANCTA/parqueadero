from fastapi import APIRouter

from schemas.parking import ParkingEntryRequest, ParkingEntryResponse, ParkingExitRequest, ParkingExitResponse
from security import require_permissions
from services.exit_service import ExitService
from services.entry_service import EntryService


router = APIRouter(prefix="/parking", tags=["parking"])
entry_service = EntryService()
exit_service = ExitService()


@router.post("/entry", response_model=ParkingEntryResponse, dependencies=[require_permissions("parking.entry")])
def create_entry(payload: ParkingEntryRequest) -> ParkingEntryResponse:
    return entry_service.process_entry(payload)


@router.post("/exit", response_model=ParkingExitResponse, dependencies=[require_permissions("parking.exit")])
def create_exit(payload: ParkingExitRequest) -> ParkingExitResponse:
    return exit_service.process_exit(payload)
