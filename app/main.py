from fastapi import FastAPI

from app.config import settings
from app.routers import users_router

app = FastAPI(title=settings.APP_NAME, version="0.1.0")
app.include_router(users_router)


@app.get("/actuator/health", tags=["health"])
async def health_check():
    return {"status": "UP"}
