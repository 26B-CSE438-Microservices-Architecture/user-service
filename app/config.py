from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "user-service"
    APP_PORT: int = 8000
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@user-db:5432/userdb"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
