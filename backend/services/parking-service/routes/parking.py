from fastapi import APIRouter

from schemas.parking import ParkingEntryRequest, ParkingEntryResponse
from services.entry_service import EntryService


router = APIRouter(prefix="/parking", tags=["parking"])
entry_service = EntryService()


@router.post("/entry", response_model=ParkingEntryResponse)
def create_entry(payload: ParkingEntryRequest) -> ParkingEntryResponse:
    return entry_service.process_entry(payload)
