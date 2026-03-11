from fastapi import FastAPI

from app.admin import setup_admin
from app.config import settings
from app.routers import internal_users_router, users_router

app = FastAPI(title=settings.APP_NAME, version="0.1.0")
app.include_router(users_router)
app.include_router(internal_users_router)
setup_admin(app)


@app.get("/actuator/health", tags=["health"])
async def health_check():
    return {"status": "UP"}
