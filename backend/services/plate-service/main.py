from fastapi import FastAPI

from config import settings
from routes.plates import router as plates_router
from routes.system import router


app = FastAPI(title=settings.service_name, version=settings.service_version)
app.include_router(router)
app.include_router(plates_router)
