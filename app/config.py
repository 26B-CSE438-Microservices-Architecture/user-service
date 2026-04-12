from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "user-service"
    APP_PORT: int = 8000
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@user-db:5432/userdb"
    RESET_PASSWORD_URL_BASE: str = "http://localhost:3000/reset-password"
    RESET_PASSWORD_TOKEN_TTL_MINUTES: int = 30
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_FROM_EMAIL: str = "no-reply@example.com"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
