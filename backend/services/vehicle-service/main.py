from fastapi import FastAPI

from config import settings
from routes.system import router


app = FastAPI(title=settings.service_name, version=settings.service_version)
app.include_router(router)
