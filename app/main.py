from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.admin import setup_admin
from app.config import settings
from app.messaging import connection as mq_connection
from app.messaging.consumer import start_consumers
from app.routers import internal_users_router, users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mq_connection.connect()
    await start_consumers()
    yield
    await mq_connection.disconnect()


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)
app.include_router(users_router)
app.include_router(internal_users_router)
setup_admin(app)


@app.get("/actuator/health", tags=["health"])
async def health_check():
    return {"status": "UP"}
