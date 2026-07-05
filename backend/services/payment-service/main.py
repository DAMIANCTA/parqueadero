from fastapi import FastAPI

from config import settings
from routes.payments import router as payments_router
from routes.system import router as system_router


app = FastAPI(title=settings.service_name, version=settings.service_version)
app.include_router(system_router)
app.include_router(payments_router)
