from fastapi import FastAPI

from app.config import settings

app = FastAPI(title=settings.APP_NAME, version="0.1.0")


@app.get("/actuator/health", tags=["health"])
async def health_check():
    return {"status": "UP"}
