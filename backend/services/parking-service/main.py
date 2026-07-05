from fastapi import FastAPI

from config import settings
from routes.parking import router as parking_router
from routes.system import router as system_router


app = FastAPI(title=settings.service_name, version=settings.service_version)
app.include_router(system_router)
app.include_router(parking_router)
